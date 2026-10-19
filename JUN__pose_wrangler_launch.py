# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# [JUN] PoseWrangler 런처 - 모듈(.mod) 없이 실행
#
# 예전에는 PoseDriverConnect.mod 로 MAYA_PLUG_IN_PATH / PYTHONPATH 를 마야에 등록해야
# 툴을 쓸 수 있었다. 이 런처는 이 파일 위치에서 경로를 직접 계산한다.
#   <PoseDriverConnect>/
#     ├── python/                      <- 이 파일 (epic_pose_wrangler 패키지 루트)
#     └── plug-ins/<windows|linux>/<마야 버전>/MayaUERBFPlugin.mll
# 1) python/ 을 sys.path 에, 2) 솔버 플러그인을 **절대 경로로** loadPlugin, 3) 창을 띄운다.
# 셸프 버튼(__dragDrop_PoseWrangler.py 가 설치)이 run() 을 부른다.

import os
import sys

import maya.cmds as cmds


PYTHON_ROOT = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(PYTHON_ROOT)
PLUGIN_NAME = "MayaUERBFPlugin"


def _platform_dir():
    return "windows" if sys.platform.startswith("win") else "linux"


def plugin_path():
    """이 마야 버전에 맞는 MayaUERBFPlugin.mll 의 절대 경로 (없어도 경로는 돌려준다)."""
    version = str(cmds.about(version=True))[:4]
    return os.path.join(MODULE_ROOT, "plug-ins", _platform_dir(), version,
                        PLUGIN_NAME + ".mll")


def ensure_plugin(autoload=False):
    """솔버 플러그인을 로드한다. 이미 로드됐으면(모듈 경로로 로드된 경우 포함) 그대로 둔다.

    Args:
        autoload: True 면 마야 Plug-in Manager 의 Auto load 를 켠다 - 솔버 노드가 든
                  씬을 툴보다 먼저 열어도 노드가 unknown 이 되지 않는다.

    Returns:
        로드한 플러그인 경로 (이미 로드돼 있었으면 None).
    """
    if PYTHON_ROOT not in sys.path:
        sys.path.append(PYTHON_ROOT)

    path = plugin_path()
    already = cmds.pluginInfo(PLUGIN_NAME, q=True, loaded=True)
    if not already:
        if not os.path.isfile(path):
            raise RuntimeError("PoseWrangler plugin not found for this Maya version: "
                               "{0}".format(path))
        cmds.loadPlugin(path, quiet=True)
    if autoload and os.path.isfile(path):
        cmds.pluginInfo(path, edit=True, autoload=True)
    return None if already else path


def run():
    """셸프 버튼 진입점 - 플러그인 로드 후 PoseWrangler 창을 띄운다."""
    loaded = ensure_plugin()
    if loaded:
        print("[JUN] PoseWrangler plugin loaded: {0}".format(loaded))
    from epic_pose_wrangler import main
    return main.PoseWrangler()
