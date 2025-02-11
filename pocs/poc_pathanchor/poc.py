
import os
from pprint import pprint
from superconf.anchors2 import PathAnchor, FileAnchor






TEST = True

if TEST:

    #project_dir = "/fake_root/absolute/test/project"
    project_dir = "../../project"
    project_dir2 = "/fake_root2"
    config = {

        "abs_complex": f"{project_dir2}/subdir2/../../subdir2/file",
        "abs_other": f"{project_dir2}../../subdir2/subdir2/file",
        "abs_parent": f"{project_dir2}/../../..",
        "abs_simple": f"{project_dir2}/justafile.yml",
        "abs_subdir": f"{project_dir2}/subdir/subdir/file",

        "rel_complex": "subdir2/../../subdir2/file",
        "rel_other": "../../subdir2/subdir2/file",
        "rel_parent": "../../..",
        "rel_simple": "justafile.yml",
        "rel_subdir": "subdir/subdir/file",

    }


    def test1_default():

        pd = PathAnchor(project_dir)

        retpath = {
            "aa_root": pd.get_dir()
        }
        retobj = {
            "aa_root": pd
        }

        for clean in [False, True]:
            print ("Cleaned", clean)
            for name, path in config.items():
                p = PathAnchor(path, anchor=pd)
                ret = p.get_dir(clean=clean)

                retpath[name] = ret
                retobj[name] = p

                # Tests
                if name.startswith("rel"):
                    assert not ret.startswith("/")
                if name.startswith("abs"):
                    assert ret.startswith("/")

            pprint (retpath)
            pprint (retobj)

    test1_default()


    data2 = {
        "rel_complex": "subdir2/../../subdir2/file",
        "rel_other": "../../subdir2/subdir2/file",
        "rel_parent": "../../..",
        "rel_simple": "justafile.yml",
        "rel_subdir": "subdir/subdir/file",

    }

    def test2_nested():

        project_dir = "/fake/prj"
        pd = PathAnchor(project_dir)

        pd_inventory = PathAnchor("inventory/", anchor=pd)
        pd_conf = PathAnchor("../../common_conf", anchor=pd)




        retpath = {
            "aa_root": pd.get_dir(),
            # "aa_conf": pd_conf.get_dir(),
            # "aa_inventory": pd_inventory.get_dir(),
        }
        retobj = {
            "aa_root": pd,
            # "aa_conf": pd_conf,
            # "aa_inventory": pd_inventory,
        }


        for cpd in [pd_inventory, pd_conf]:

            for clean in [False, True]:

                print ("Cleaned", cpd, clean)
                retpath["aa_current"] = cpd.get_dir(clean=clean)
                retobj["aa_current"] = cpd

                for name, path in data2.items():
                    p = PathAnchor(path, anchor=cpd)
                    ret = p.get_dir(clean=clean)

                    retpath[name] = ret
                    retobj[name] = p

                    # # Tests
                    # if name.startswith("rel"):
                    #     assert not ret.startswith("/")
                    # if name.startswith("abs"):
                    #     assert ret.startswith("/")

                pprint (retobj)
                pprint (retpath)

    test2_nested()



    def test3_parents():

        project_dir = "/fake/prj"
        pd0 = PathAnchor(project_dir)
        pd1 = PathAnchor("../../common_conf", anchor=pd0)
        pd2 = PathAnchor("inventory/", anchor=pd1)

        # pprint (pd0.__dict__)
        # pprint (pd1.__dict__)
        # pprint (pd2.__dict__)

        # Test anchor inheritance
        ret = pd2.get_parents()
        pprint (ret)
        
        ret = pd0.get_parents()
        pprint (ret)

        # Test path resolution
        ret = {
            "pd0a": PathAnchor("subconf/", anchor=pd0).get_dir(),
            "pd1a": PathAnchor("subconf/", anchor=pd1).get_dir(),
            "pd2a": PathAnchor("subconf/", anchor=pd2).get_dir(),
        }
        pprint(ret)


    test3_parents()


    def test4_modes():

        project_dir = "/fake/prj"
        #project_dir = "fake/prj"
        pd0 = PathAnchor(project_dir)
        pd1 = PathAnchor("../../common_conf", anchor=pd0, mode="abs")
        pd2 = PathAnchor("inventory/", anchor=pd1, mode="rel")

        # pprint (pd0.__dict__)
        # pprint (pd1.__dict__)
        # pprint (pd2.__dict__)

        pd0a = PathAnchor("subconf/", anchor=pd0)
        pd1a = PathAnchor("subconf/", anchor=pd1)
        pd2a = PathAnchor("subconf/", anchor=pd2)

        print("RESULT")
        ret = pd0a.get_dir()
        pprint (ret)
        assert ret.startswith("/") == os.path.isabs(project_dir)

        ret = pd1a.get_dir()
        pprint (ret)
        assert ret.startswith("/")
        
        # pprint (pd2a.__dict__)
        ret = pd2a.get_dir()
        pprint (ret)
        assert not ret.startswith("/")

    test4_modes()



    def test5_files():

        print ("\n TEST 5 FileAnchors")

        project_dir = "/fake/prj"
        #project_dir = "fake/prj"
        pd0 = PathAnchor(project_dir)
        pd1 = PathAnchor("../../common_conf", anchor=pd0, mode="abs")
        pd2 = PathAnchor("inventory/", anchor=pd1, mode="rel")



        pd0a = FileAnchor("subconf/myfile1.yml", anchor=pd0)
        pd1a = FileAnchor("subconf/myfile2.yml", anchor=pd1)
        pd2a = FileAnchor("subconf/myfile3.yml", anchor=pd2)

        print("RESULT")
        ret = {
            "obj":  pd0a,
            "path": pd0a.get_path(),
            "file": pd0a.get_file(),
            "dir": pd0a.get_dir(),
        }
        pprint (ret)

        ret = {
            "obj":  pd1a,
            "path": pd1a.get_path(),
            "file": pd1a.get_file(),
            "dir":  pd1a.get_dir(),
        }
        pprint (ret)

        ret = {
            "obj":  pd2a,
            "path": pd2a.get_path(),
            "file": pd2a.get_file(),
            "dir":  pd2a.get_dir(),
        }
        pprint (ret)

    test5_files()

