import pytest
from lib.store_base import Source, UndefinedVarError
from lib.store_template import RenderableStoreManager


@pytest.fixture
def varmgr():
    """Create a basic variable manager with predefined sources and scopes"""
    mgr = RenderableStoreManager()

    # Add sources with different levels
    mgr.add_sources(
        [
            Source("app_cli", level=300, help="Application main CLI"),
            Source("app_env", level=300, help="Application environment variables"),
            Source("app_defaults", level=999, help="Application defaults"),
            Source("project_cli", level=300, help="Project main CLI"),
            Source("project_env", level=300, help="Project environment variables"),
            Source("project_defaults", level=999, help="Project defaults"),
            Source("stack_cli", level=300, help="Stack main CLI"),
            Source("stack_env", level=300, help="Stack environment variables"),
            Source("stack_defaults", level=999, help="Stack defaults"),
        ]
    )

    # Set up scopes with inheritance
    mgr.set_scopes(
        {
            "scope_app": [
                "app_cli",
                "app_env",
                "app_defaults",
            ],
            "scope_project": [
                "project_cli",
                "project_env",
                "project_defaults",
                # Defaults
                "scope_app",
            ],
            "scope_stack": [
                "stack_cli",
                "stack_env",
                "stack_defaults",
                # Defaults
                "scope_project",
            ],
        }
    )

    return mgr


def test_basic_variable_resolution(varmgr):
    """Test basic variable resolution without templates"""
    vars_app = {
        "app_name": "dataset1",
    }
    varmgr.set_layer("app_cli", vars_app)

    renderer = varmgr.get_renderer("scope_app")
    assert renderer.render_var("app_name") == "dataset1"


def test_template_variable_resolution(varmgr):
    """Test resolving template variables with references"""
    vars_app = {"app_name": "dataset1"}
    vars_project = {"project_name": "project1+${stack_name}"}
    vars_stack = {
        "stack_name": "dataset3",
        "stack_fname": "${project_name}_${stack_name}",
    }

    varmgr.set_layer("app_cli", vars_app)
    varmgr.set_layer("project_env", vars_project)
    varmgr.set_layer("stack_env", vars_stack)

    renderer = varmgr.get_renderer("scope_stack")

    # Test individual variable resolution
    assert renderer.render_var("stack_name") == "dataset3"
    assert renderer.render_var("project_name") == "project1+dataset3"
    assert renderer.render_var("stack_fname") == "project1+dataset3_dataset3"


def test_render_values(varmgr):
    """Test rendering all values in a scope"""
    vars_app = {"app_name": "dataset1"}
    vars_project = {"project_name": "project1+${stack_name}"}
    vars_stack = {
        "stack_name": "dataset3",
        "stack_fname": "${project_name}_${stack_name}",
    }

    varmgr.set_layer("app_cli", vars_app)
    varmgr.set_layer("project_env", vars_project)
    varmgr.set_layer("stack_env", vars_stack)

    renderer = varmgr.get_renderer("scope_stack")
    rendered_values = renderer.render_values()

    expected = {
        "app_name": "dataset1",
        "project_name": "project1+dataset3",
        "stack_fname": "project1+dataset3_dataset3",
        "stack_name": "dataset3",
    }
    assert rendered_values == expected


def test_caching_behavior(varmgr):
    """Test caching behavior of rendered variables"""
    vars_app = {"app_name": "dataset1"}
    vars_project = {"project_name": "project1+${stack_name}"}
    vars_stack = {
        "stack_name": "dataset3",
        "stack_fname": "${project_name}_${stack_name}",
    }

    varmgr.set_layer("app_cli", vars_app)
    varmgr.set_layer("project_env", vars_project)
    varmgr.set_layer("stack_env", vars_stack)

    renderer = varmgr.get_renderer("scope_stack")

    # Test without cache
    result1 = renderer.render_var("stack_fname", cache=False)
    result2 = renderer.render_var("stack_fname", cache=False)
    assert result1 == result2

    # Test with cache
    result1 = renderer.render_var("stack_fname", cache=True)
    result2 = renderer.render_var("stack_fname", cache=True)
    assert result1 == result2


def test_debug_output(varmgr):
    """Test debug output format"""
    vars_app = {"app_name": "dataset1"}
    vars_project = {"project_name": "project1+${stack_name}"}
    vars_stack = {
        "stack_name": "dataset3",
        "stack_fname": "${project_name}_${stack_name}",
    }

    varmgr.set_layer("app_cli", vars_app)
    varmgr.set_layer("project_env", vars_project)
    varmgr.set_layer("stack_env", vars_stack)

    renderer = varmgr.get_renderer("scope_stack")
    value, debug_info = renderer.render_var("stack_fname", debug=True)

    assert value == "project1+dataset3_dataset3"
    assert "key" in debug_info
    assert "level" in debug_info
    assert "templated" in debug_info
    assert "children" in debug_info


def test_circular_reference_detection(varmgr):
    """Test detection of circular references"""
    vars_project = {"project_name": "project1+${stack_fname}"}
    vars_stack = {"stack_fname": "${project_name}_suffix"}

    varmgr.set_layer("project_env", vars_project)
    varmgr.set_layer("stack_env", vars_stack)

    renderer = varmgr.get_renderer("scope_stack")

    with pytest.raises(ValueError, match="Circular reference detected:.*"):
        renderer.render_var("stack_fname")


def test_undefined_variable(varmgr):
    """Test handling of undefined variables"""
    renderer = varmgr.get_renderer("scope_stack")

    with pytest.raises(UndefinedVarError):
        renderer.render_var("nonexistent_var")


def test_multiple_renderers(varmgr):
    """Test that multiple renderers for the same scope share the same instance"""
    renderer1 = varmgr.get_renderer("scope_stack")
    renderer2 = varmgr.get_renderer("scope_stack")

    assert renderer1 is renderer2


def test_non_template_values(varmgr):
    """Test handling of non-template values"""
    vars_stack = {
        "string_value": "simple string",
        "number_value": 42,
        "bool_value": True,
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("string_value") == "simple string"
    assert renderer.render_var("number_value") == 42
    assert renderer.render_var("bool_value") is True


def test_empty_template_string(varmgr):
    """Test handling of empty template strings"""
    vars_stack = {
        "empty_string": "",
        "template_with_spaces": "   ${other_var}   ",
        "other_var": "value",
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("empty_string") == ""
    assert renderer.render_var("template_with_spaces") == "   value   "


def test_nested_template_resolution(varmgr):
    """Test deeply nested template resolution"""
    vars_stack = {
        "var1": "one",
        "var2": "${var1}_two",
        "var3": "${var2}_three",
        "var4": "${var3}_four",
        "var5": "${var4}_five",
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("var5") == "one_two_three_four_five"


def test_special_characters_in_templates(varmgr):
    """Test handling of special characters in template strings"""
    vars_stack = {
        "special_chars": "!@#$%^&*()",
        # "special_chars": "! @ # $ % ^ & * ( ) ",
        # "special_chars": "! @ # $ %  ^ & * ( ) ",
        # "special_chars": "test'$'test",
        "url": "https://example.com",
        "path": "/path/to/file",
        "template": "${special_chars}_${url}_${path}"
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    out = renderer.render_var("template")
    expected = "!@#$%^&*()_https://example.com_/path/to/file"
    # print(f"out     : {out}")
    # print(f"expected: {expected}")
    assert out == expected


def test_multiple_references_same_var(varmgr):
    """Test multiple references to the same variable"""
    vars_stack = {
        "base": "value",
        "double_ref": "${base}_${base}",
        "triple_ref": "${base}_${base}_${base}",
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("double_ref") == "value_value"
    assert renderer.render_var("triple_ref") == "value_value_value"

from pprint import pprint


# TOFIX
def test_escaped_dollar_signs(varmgr):
    """Test handling of escaped dollar signs in templates"""
    vars_stack = {
        "var": "value",
        "unexisting": "$not_a_var",
        "escaped2": "$$not_a_template",
        "escaped3": "$$$not_a_template",
        "escaped4": "$$$$not_a_template",
        "mixed": "$$literal_${var}_$$another"
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    out = renderer.render_values(value_on_undefined="<UNDEFINED>")
    print("OUT: ")
    pprint(out)

    # assert False

    out = renderer.render_var("unexisting", debug=True, value_on_undefined="")
    print("OUT: ")
    pprint(out)

    assert renderer.render_var("escaped2") == "$not_a_template"
    assert renderer.render_var("mixed") == "$literal_value_$another"


def test_scope_inheritance_with_templates(varmgr):
    """Test template resolution across different scopes with inheritance"""
    vars_app = {"base_var": "app_value"}
    vars_project = {"project_var": "${base_var}_project"}
    vars_stack = {"stack_var": "${project_var}_stack"}

    varmgr.set_layer("app_defaults", vars_app)
    varmgr.set_layer("project_defaults", vars_project)
    varmgr.set_layer("stack_defaults", vars_stack)

    # Test resolution at different scope levels
    app_renderer = varmgr.get_renderer("scope_app")
    project_renderer = varmgr.get_renderer("scope_project")
    stack_renderer = varmgr.get_renderer("scope_stack")

    assert app_renderer.render_var("base_var") == "app_value"
    assert project_renderer.render_var("project_var") == "app_value_project"
    assert stack_renderer.render_var("stack_var") == "app_value_project_stack"


def test_template_with_missing_closing_brace(varmgr):
    """Test handling of malformed templates with missing closing braces"""
    vars_stack = {
        "var": "value",
        "malformed": "${var_without_closing"
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    # Should return the original string without modification
    assert renderer.render_var("malformed") == "${var_without_closing"


# def test_cache_invalidation_behavior(varmgr):
#     """Test cache behavior when variables are modified"""
#     vars_stack = {
#         "base": "original",
#         "dependent": "${base}_suffix"
#     }

#     # ROUND 1
#     varmgr.set_layer("stack_env", vars_stack)
#     pprint(varmgr.__dict__)

#     renderer = varmgr.get_renderer("scope_stack")
#     pprint(renderer.__dict__)

#     # First render to populate cache
#     assert renderer.render_var("dependent", cache=True) == "original_suffix"

#     # ROUND 2
#     # Modify the base variable
#     varmgr.set_layer("stack_env", {"base": "modified"})

#     out = varmgr.get_var("base", debug=True)
#     pprint(out)

#     # Test with and without cache
#     assert renderer.render_var("dependent", cache=True) == "original_suffix"  # Should use cached value
#     assert renderer.render_var("dependent", cache=False) == "modified_suffix"  # Should reflect new value


def test_complex_nested_references(varmgr):
    """Test complex nested references with multiple variable types"""
    vars_stack = {
        "num": 42,
        "bool_val": True,
        "str_val": "string",
        "complex": "${str_val}_${num}_${bool_val}",
        "nested": "${complex}_${complex}",
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("complex") == "string_42_True"
    assert renderer.render_var("nested") == "string_42_True_string_42_True"


# def test_template_substitution_edge_cases(varmgr):
#     """Test various edge cases and special characters in template substitution"""
#     vars_stack = {
#         # Test various special characters
#         "special1": "!@#$%^&*()",
#         "special2": "[]{}\\|;:'\",.<>/?",
#         "special3": "~`",
#         "special4": " \t\n\r",  # whitespace characters
#         "special5": "™®©",      # unicode symbols
#         "special6": "🌟🚀🎉",    # emojis

#         # Test dollar sign edge cases
#         "dollar1": "$",
#         "dollar2": "$$",
#         "dollar3": "$$$",
#         "dollar4": "${",
#         "dollar5": "$}",
#         "dollar6": "test'$'test",
#         "dollar7": "$ {var}",   # space after $

#         # Test various template patterns
#         "var": "base_value",
#         "template1": "${var}${var}",          # adjacent templates
#         "template2": "${var} ${var}",         # spaced templates
#         "template3": "$$${var}",              # escaped dollar with template
#         "template4": "${var}$$",              # template with escaped dollar
#         "template5": "$$${var}$$",            # multiple escaped dollars
#         "template6": "${special1}${special2}", # templates with special chars
#         "template7": "prefix${var}suffix",     # with affixes
#         "template8": "  ${var}  ",            # with whitespace
#         "template9": "\t${var}\n",            # with special whitespace
#         "template10": "${special5}${special6}", # with unicode and emojis

#         # Test nested templates with special characters
#         "nested1": "${template6}${template7}",
#         "nested2": "${template8}${template9}",

#         # Test potentially problematic patterns
#         "problem1": "${var${var}}",           # nested braces (invalid)
#         "problem2": "${var}}}",               # extra closing braces
#         "problem3": "${var{{}}",              # mixed braces
#         "problem4": "}{${var}}{",             # reversed braces
#         "problem5": "${not_existing}",        # undefined variable
#         "problem6": "${var_without_closing",  # unclosed template

#         # Test long strings and repetitions
#         "long1": "${var}" * 10,              # repeated templates
#         "long2": "$" * 50,                   # many dollar signs
#         "long3": "${" * 10,                  # many opening sequences
#         "long4": "}" * 10,                   # many closing braces
#     }

#     varmgr.set_layer("stack_env", vars_stack)
#     renderer = varmgr.get_renderer("scope_stack")

#     # Test special characters
#     assert renderer.render_var("special1") == "!@#$%^&*()"
#     assert renderer.render_var("special2") == "[]{}\\|;:'\",.<>/?"
#     assert renderer.render_var("special3") == "~`"
#     assert renderer.render_var("special4") == " \t\n\r"
#     assert renderer.render_var("special5") == "™®©"
#     assert renderer.render_var("special6") == "🌟🚀🎉"

#     # Test dollar sign edge cases
#     assert renderer.render_var("dollar1") == "$"
#     assert renderer.render_var("dollar2") == "$$"
#     assert renderer.render_var("dollar3") == "$$$"
#     assert renderer.render_var("dollar4") == "${"
#     assert renderer.render_var("dollar5") == "$}"
#     assert renderer.render_var("dollar6") == "test'$'test"
#     assert renderer.render_var("dollar7") == "$ {var}"

#     # Test template patterns
#     assert renderer.render_var("template1") == "base_valuebase_value"
#     assert renderer.render_var("template2") == "base_value base_value"
#     assert renderer.render_var("template3") == "$$base_value"
#     assert renderer.render_var("template4") == "base_value$$"
#     assert renderer.render_var("template5") == "$$base_value$$"
#     assert renderer.render_var("template6") == "!@#$%^&*()[]{}\\|;:'\",.<>/?"
#     assert renderer.render_var("template7") == "prefixbase_valuesuffix"
#     assert renderer.render_var("template8") == "  base_value  "
#     assert renderer.render_var("template9") == "\tbase_value\n"
#     assert renderer.render_var("template10") == "™®©🌟🚀🎉"

#     # Test nested templates
#     assert renderer.render_var("nested1") == "!@#$%^&*()[]{}\\|;:'\",.<>/?prefixbase_valuesuffix"
#     assert renderer.render_var("nested2") == "  base_value  \tbase_value\n"

#     # Test problematic patterns (should not raise exceptions)
#     renderer.render_var("problem1")  # Should handle nested braces gracefully
#     renderer.render_var("problem2")  # Should handle extra closing braces
#     renderer.render_var("problem3")  # Should handle mixed braces
#     renderer.render_var("problem4")  # Should handle reversed braces
#     with pytest.raises(UndefinedVarError):
#         renderer.render_var("problem5")  # Should raise UndefinedVarError
#     renderer.render_var("problem6")  # Should handle unclosed template

#     # Test long strings and repetitions
#     assert renderer.render_var("long1") == "base_value" * 10
#     assert renderer.render_var("long2") == "$" * 50
#     assert renderer.render_var("long3") == "${" * 10
#     assert renderer.render_var("long4") == "}" * 10


def test_template_debug_mode(varmgr):
    """Test template rendering in debug mode with special characters"""
    vars_stack = {
        "base": "value!@#$",
        "nested": "${base}_${base}",
        "complex": "prefix_${nested}_suffix"
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    # Test debug output for simple variable
    value, debug_info = renderer.render_var("base", debug=True)
    assert value == "value!@#$"
    assert debug_info["key"] == "base"
    assert isinstance(debug_info["templated"], bool)

    # Test debug output for nested template
    value, debug_info = renderer.render_var("nested", debug=True)
    assert value == "value!@#$_value!@#$"
    assert debug_info["templated"]
    assert "children" in debug_info
    assert len(debug_info["children"]) == 1

    # Test debug output for complex template
    value, debug_info = renderer.render_var("complex", debug=True)
    assert value == "prefix_value!@#$_value!@#$_suffix"
    assert debug_info["templated"]
    assert "children" in debug_info
    assert "nested" in debug_info["children"]
