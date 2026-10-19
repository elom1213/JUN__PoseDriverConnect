# Changelog — PoseDriverConnect `[JUN]` 포크

이 포크(`epic_pose_wrangler` 파이썬 패키지)의 수정 내역. **최신이 위.**
베이스는 Epic Games PoseWrangler `v2.5.0` (직렬화 포맷 `1.2.0`) — 첫 커밋 `699e71e` 가 벤더 원본이다.
배경과 패치 설명은 [`README.md`](README.md).

## 2026-10-19 — 드래그&드롭 셸프 설치 (`.mod` 불필요)

- **`__dragDrop_PoseWrangler.py`** (신규): 마야 뷰포트로 드롭하면 현재 셸프에 `PoseWrangler` 버튼 설치.
  같은 파일을 다시 드롭하면 옛 버튼을 지우고 새로 만든다. 드롭할 때 솔버 플러그인을 로드하고 **Auto load** 를 켠다.
- **`JUN__pose_wrangler_launch.py`** (신규): 셸프 버튼 진입점 `run()`.
  `python/` 을 `sys.path` 에 넣고 `plug-ins/<windows|linux>/<마야 버전>/MayaUERBFPlugin.mll` 을
  **절대 경로로** `loadPlugin` 한 뒤 `main.PoseWrangler()`. 이미 로드돼 있으면(예: `.mod`) 그대로 쓴다.
- **`icon/PoseWrangler.svg` / `.png`** (신규): 32px 셸프 아이콘.
- 이전에는 `PoseDriverConnect.mod` 로 `MAYA_PLUG_IN_PATH` / `PYTHONPATH` 를 등록해야 했다.
  이제 모듈 폴더(`plug-ins/` + `python/`)만 있으면 어디에 둬도 된다. `.mod` 방식도 그대로 동작.
- 벤더 코드(`epic_pose_wrangler/`)는 손대지 않았다.
- 검증: mayapy 2024, `MAYA_APP_DIR` 을 빈 폴더로 둬 `.mod` 가 없는 상태에서 셸프 명령을 그대로 실행 →
  플러그인 로드 · `UERBFSolverNode` 사용 가능 · `Pose Wrangler [JUN] 2.5.0` 창 생성 · Auto load 켜짐.
  마야 GUI 에서의 실제 드롭은 미확인.
- 커밋: `d261446`

## 2026-08-03 — 포크 문서화

- `README.md` 추가 — 포크 이유, 직렬화 패치 3단계, 설치 · 구조 · 제약. 커밋: `e0be1be`

## 2026-05-29 — 빈 솔버 스킵

- `serializer_v1_2_0.py`: driven 이 0개가 된 솔버는 `RBFNode.create_from_data` 단계에서 건너뛰고
  `Ignore Solver : <이름>` 출력 (껍데기 솔버 노드 생성 방지). 디버그 print 정리.
- `lunchCmd.py`(셸프용 실행 스니펫), `JUN__sample/sample_01.json`(회귀 확인용 MetaHuman 전신 프리셋) 추가.
- 커밋: `49a1e1a`

## 2026-05-28 — 존재하지 않는 driven 무시 · 창 타이틀

- `serializer_v1_2_0.py`: 델타 모드 임포트에서 `driven_transforms` 를 `cmds.objExists` 로 필터,
  포즈 델타 복원 루프에서 없는 driven 을 건너뜀 (KeyError 방지). 커밋: `7279674`
- `v2/view/pose_wrangler_window.py`: 창 타이틀을 `Pose Wrangler [JUN] 2.5.0` 으로. 커밋: `6ef0f48`

## 2026-05-28 — first commit

- Epic Games PoseDriverConnect 벤더 원본 (파이썬 소스 67개 파일). 커밋: `699e71e`
