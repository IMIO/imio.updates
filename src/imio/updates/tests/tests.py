# -*- coding: utf-8 -*-
#
# tests
# IMIO <support@imio.be>
#
from imio.updates.update_instances import check_buildout
from imio.updates.update_instances import run_function_parts
from unittest.mock import patch

import os
import subprocess
import tempfile

import unittest


class TestUpdateInstances(unittest.TestCase):
    """ """

    @patch("imio.updates.update_instances.run_function")
    @patch("imio.updates.update_instances.doit", True)
    @patch("imio.updates.update_instances.get_instance_home", return_value="")
    @patch("imio.updates.update_instances.get_batch_config")
    def test_run_function_parts(self, mock_get_batch_config, mock_get_instance_home, mock_run_function):
        """ """
        call_res = []
        params = {}
        batch_config = {}

        def reset(c_r, prs):
            c_r.clear()
            prs["env"] = ""

        def mock_run_function_se(*args, **kwargs):
            call_res.append(kwargs)
            return 0  # Simulate successful execution

        mock_run_function.side_effect = mock_run_function_se

        # BATCH TOTALS
        # ll < bn
        reset(call_res, params)
        params["env"] = "SPACEX=GREAT"
        run_function_parts("a", {"batch": 10, "a": 5}, params)
        self.assertEqual(len(call_res), 1)
        self.assertEqual(call_res[0]["run_nb"], 1)
        self.assertEqual(call_res[0]["env"], "SPACEX=GREAT FUNC_PART=a BATCH=10 IU_RUN1=1")
        # ll = bn
        reset(call_res, params)
        run_function_parts("a", {"batch": 10, "a": 10}, params)
        self.assertEqual(len(call_res), 1)
        self.assertEqual(call_res[0]["run_nb"], 1)
        self.assertEqual(call_res[0]["env"], "FUNC_PART=a BATCH=10 IU_RUN1=1")
        # ll > bn and exact multiple
        reset(call_res, params)
        run_function_parts("a", {"batch": 10, "a": 20}, params)
        self.assertEqual(len(call_res), 2)
        self.assertListEqual([dic["run_nb"] for dic in call_res], [1, 2])
        self.assertListEqual(
            [dic["env"] for dic in call_res], ["FUNC_PART=a BATCH=10 IU_RUN1=1", "FUNC_PART=a BATCH=10 BATCH_LAST=1"]
        )
        # ll > bn and not multiple
        reset(call_res, params)
        run_function_parts("a", {"batch": 10, "a": 22}, params)
        self.assertEqual(len(call_res), 3)
        self.assertListEqual([dic["run_nb"] for dic in call_res], [1, 2, 3])
        self.assertListEqual(
            [dic["env"] for dic in call_res],
            ["FUNC_PART=a BATCH=10 IU_RUN1=1", "FUNC_PART=a BATCH=10", "FUNC_PART=a BATCH=10 BATCH_LAST=1"],
        )

        def mock_get_batch_config_se(var):
            return batch_config

        mock_get_batch_config.side_effect = mock_get_batch_config_se

        # BATCHING
        params["bldt"] = "xx"
        params["buildouts"] = {"xx": {"path": "yy"}}
        # ll < bn
        # batch_config is the result after the first run
        reset(call_res, params)
        params["env"] = "SPACEX=GREAT"
        batch_config.update({"pf": "", "cf": "", "af": []})
        batch_config.update({"ll": 5, "kc": 5, "bn": 10})
        run_function_parts("a", {"batch": 10, "batching": ["a"]}, params)
        self.assertEqual(len(call_res), 1)
        self.assertEqual(call_res[0]["run_nb"], 1)
        self.assertEqual(call_res[0]["env"], "SPACEX=GREAT FUNC_PART=a BATCH=10 IU_RUN1=1")
        # ll = bn
        reset(call_res, params)
        batch_config.update({"ll": 10, "kc": 10, "bn": 10})
        run_function_parts("a", {"batch": 10, "batching": ["a"]}, params)
        self.assertEqual(len(call_res), 1)
        self.assertEqual(call_res[0]["run_nb"], 1)
        self.assertEqual(call_res[0]["env"], "FUNC_PART=a BATCH=10 IU_RUN1=1")
        # ll > bn and exact multiple
        reset(call_res, params)
        batch_config.update({"ll": 20, "kc": 10, "bn": 10})
        run_function_parts("a", {"batch": 10, "batching": ["a"]}, params)
        self.assertEqual(len(call_res), 2)
        self.assertListEqual([dic["run_nb"] for dic in call_res], [1, 2])
        self.assertListEqual(
            [dic["env"] for dic in call_res],
            ["FUNC_PART=a BATCH=10 IU_RUN1=1", "FUNC_PART=a BATCH=10 BATCH_LAST=1"],
        )
        # ll > bn and not multiple
        reset(call_res, params)
        batch_config.update({"ll": 22, "kc": 10, "bn": 10})
        run_function_parts("a", {"batch": 10, "batching": ["a"]}, params)
        self.assertEqual(len(call_res), 3)
        self.assertListEqual([dic["run_nb"] for dic in call_res], [1, 2, 3])
        self.assertListEqual(
            [dic["env"] for dic in call_res],
            [
                "FUNC_PART=a BATCH=10 IU_RUN1=1",
                "FUNC_PART=a BATCH=10",
                "FUNC_PART=a BATCH=10 BATCH_LAST=1",
            ],
        )


    def test_check_buildout(self):
        path = os.path.join(tempfile.mkdtemp(), "bldt")
        git = ["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(["git", "init", "-q", path], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "1"], check=True)
        subprocess.run(git + ["tag", "1.0"], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "2"], check=True)
        subprocess.run(git + ["tag", "2.0"], check=True)
        self.assertTrue(check_buildout(path, "1.0", True))  # commit after tag
        self.assertTrue(check_buildout(path, "2.0", True))  # on tag
        subprocess.run(git + ["checkout", "-q", "1.0"], check=True)
        self.assertFalse(check_buildout(path, "2.0", True))  # before tag
        self.assertFalse(check_buildout(path, "3.0", True))  # unknown tag
        self.assertFalse(check_buildout(path, "1.0", False))  # no puppet log
        log = os.path.join(path, "puppet-buildout-bldt.log")
        with open(log, "w") as fh:
            fh.write("mr.developer: There have been errors\nmake: *** [Makefile:42: buildout] Error 1\n")
        self.assertFalse(check_buildout(path, "1.0", False))
        with open(log, "w") as fh:
            fh.write("Installing instance1.\nGenerated script '/srv/instances/bldt/bin/instance1'.\n")
        self.assertTrue(check_buildout(path, "1.0", False))
        os.utime(log, (0, 0))  # log older than the checkout
        self.assertFalse(check_buildout(path, "1.0", False))


if __name__ == "__main__":
    unittest.main()
