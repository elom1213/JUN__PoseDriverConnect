# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# [JUN] PoseWrangler - 셸프 버튼 설치 + 드래그&드롭 진입점
#
# 이 파일을 Maya 뷰포트로 드래그&드롭하면 현재 셸프에 버튼이 설치된다.
# 버튼은 JUN__pose_wrangler_launch.run() 을 부른다 - 솔버 플러그인을 절대 경로로 로드하고
# 창을 띄우므로 PoseDriverConnect.mod(플러그인 경로 등록)가 필요 없다.
# 설치할 때 플러그인 Auto load 도 켠다(솔버 노드가 든 씬을 먼저 열어도 노드가 살아 있게).

import os
import sys

import maya.cmds as cmds
import maya.mel as mel


PYTHON_ROOT = os.path.dirname(os.path.abspath(__file__))     # .../PoseDriverConnect/python

if PYTHON_ROOT not in sys.path:
    sys.path.append(PYTHON_ROOT)


TOOL_LABEL = "PoseWrangler"
_MARK = "JUN__pose_wrangler_launch.run()"

_ICON_PATH = os.path.join(PYTHON_ROOT, "icon", "PoseWrangler.png")
ICON_NAME = _ICON_PATH if os.path.exists(_ICON_PATH) else "pythonFamily.png"

SHELF_COMMAND = r'''
import sys

ROOT = r"{root}"

if ROOT not in sys.path:
    sys.path.append(ROOT)

import JUN__pose_wrangler_launch

JUN__pose_wrangler_launch.run()
'''.format(root=PYTHON_ROOT.replace("\\", "/"))


def install_shelf_button():

    current_shelf = mel.eval('$temp=$gShelfTopLevel')
    current_tab = cmds.tabLayout(current_shelf, q=True, selectTab=True)

    # 중복 버튼 제거
    for btn in cmds.shelfLayout(current_tab, q=True, childArray=True) or []:
        # childArray 는 구분선(separator) 도 준다 - shelfButton 질의가 RuntimeError.
        try:
            cmd = cmds.shelfButton(btn, q=True, command=True)
        except RuntimeError:
            continue
        if _MARK in str(cmd):
            cmds.deleteUI(btn)

    cmds.shelfButton(
        parent=current_tab,
        label=TOOL_LABEL,
        annotation="[JUN] PoseWrangler (Epic PoseDriverConnect)",
        imageOverlayLabel="PW",
        image1=ICON_NAME,
        style="iconAndTextVertical",
        command=SHELF_COMMAND,
        sourceType="python"
    )

    # 플러그인 로드 + Auto load. 실패해도 버튼 설치는 끝났으므로 경고만 남긴다.
    try:
        import JUN__pose_wrangler_launch as launch
        launch.ensure_plugin(autoload=True)
    except Exception as e:
        cmds.warning("[JUN] PoseWrangler plugin: {0}".format(e))

    cmds.inViewMessage(
        amg="<hl>{0}</hl> shelf button installed.".format(TOOL_LABEL),
        pos="midCenter",
        fade=True
    )
    print("Shelf Installed")


def onMayaDroppedPythonFile(*args):

    try:
        install_shelf_button()
    finally:
        # 베이스네임으로 import 되어 sys.modules 에 캐시된다 - 다음 드롭이 옛 모듈을 쓰지 않게 제거.
        sys.modules.pop(__name__, None)
