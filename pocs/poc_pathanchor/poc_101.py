from pprint import pprint

from superconf.anchors2 import PathAnchor, FileAnchor


PROJECT_DIRS = [
    "/fake_root/project",
    "rel_subdir/common_conf",
    "../../parent_dir/common_conf",
    "../../parent_dir/../other_root/subroot",
]


for project_dir in PROJECT_DIRS:
    print("Results for project dir: ", project_dir)
    # print("  " + "=" * 80)

    # Create a root anchor
    root_anchor = PathAnchor(project_dir)

    # Create paths relative to the root and store them in a dictionary
    anchors = {
        'nested_rel_path': PathAnchor("subdir1/subdir1", anchor=root_anchor),
        'nested_abs_path': PathAnchor(f"{project_dir}/subdir1/subdir1", anchor=root_anchor),
        'config_rel_file': FileAnchor("justafile1_rel.yml", anchor=root_anchor),
        'config_abs_file': FileAnchor(f"{project_dir}/justafile2_abs.yml", anchor=root_anchor),
        
        'subfile_rel_file': FileAnchor("subdir2/subdir2/subfile_rel.yml", anchor=root_anchor),
        'subfile_abs_file': FileAnchor(f"{project_dir}/subdir2/subdir2/subfile_abs.yml", anchor=root_anchor),
        
        'ext_abs_path': PathAnchor("/noroot/subdir3/subdir3/file", anchor=root_anchor),
        'ext_rel_path': PathAnchor("../../common_conf/file.yml", anchor=root_anchor)
    }

    print("  " + "=" * 80)
    print("  root_anchor        ", root_anchor)
    for name, anchor in anchors.items():
        print(f"  {name:<20} {anchor}")

    modes = [None,"abs", "rel"]
    for mode in modes:
        if mode:
            root_anchor.path_mode = mode
        print("\n  Mode: ", mode or "default/auto")
        print("  " + "=" * 80)

        print("  root_anchor         ", root_anchor.get_path())
        print("  root_anchor         ", root_anchor.get_path(clean=True))
        
        for name, anchor in anchors.items():
            print(f"  {name:<20} {anchor.get_path()}")
            clean_path = anchor.get_path(clean=True)
            if clean_path != anchor.get_path():
                print(f"  {name:<20} {clean_path}\t\t\t\t\t\t\t\t!!!Cleaned version!!!")
        print("")



