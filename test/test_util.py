import cv2 as cv
import pytest

from dbd_gameai import util


def test_ang_diff():
    assert util.ang_diff(-10) == -10
    assert util.ang_diff(180) == -180
    assert util.ang_diff(200) == -160
    assert util.ang_diff(-200) == 160
    assert util.ang_diff(360) == 0
