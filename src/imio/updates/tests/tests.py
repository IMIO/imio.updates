# -*- coding: utf-8 -*-
#
# tests
# IMIO <support@imio.be>
#
from imio.updates.update_instances import run_function_parts
from unittest.mock import patch

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
        run_function_parts("a", {"batch": 10, "a": 5}, params)
        self.assertEqual(len(call_res), 1)
        self.assertEqual(call_res[0]["run_nb"], 1)
        self.assertEqual(call_res[0]["env"], "FUNC_PART=a  BATCH=10")
        # ll = bn
        reset(call_res, params)
        run_function_parts("a", {"batch": 10, "a": 10}, params)
        self.assertEqual(len(call_res), 1)
        self.assertEqual(call_res[0]["run_nb"], 1)
        self.assertEqual(call_res[0]["env"], "FUNC_PART=a  BATCH=10")
        # ll > bn and exact multiple
        reset(call_res, params)
        run_function_parts("a", {"batch": 10, "a": 20}, params)
        self.assertEqual(len(call_res), 2)
        self.assertListEqual([dic["run_nb"] for dic in call_res], [1, 2])
        self.assertListEqual(
            [dic["env"] for dic in call_res], ["FUNC_PART=a  BATCH=10", "FUNC_PART=a  BATCH=10 BATCH_LAST=1"]
        )
        # ll > bn and not multiple
        reset(call_res, params)
        run_function_parts("a", {"batch": 10, "a": 22}, params)
        self.assertEqual(len(call_res), 3)
        self.assertListEqual([dic["run_nb"] for dic in call_res], [1, 2, 3])
        self.assertListEqual(
            [dic["env"] for dic in call_res],
            ["FUNC_PART=a  BATCH=10", "FUNC_PART=a  BATCH=10", "FUNC_PART=a  BATCH=10 BATCH_LAST=1"],
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
        batch_config = {"ll": 5, "kc": 5, "bn": 10}
        run_function_parts("a", {"batch": 10, "batching": ["a"]}, params)
        self.assertEqual(len(call_res), 1)
        self.assertEqual(call_res[0]["run_nb"], 1)
        self.assertEqual(call_res[0]["env"], "FUNC_PART=a  BATCH=10")


if __name__ == "__main__":
    unittest.main()
