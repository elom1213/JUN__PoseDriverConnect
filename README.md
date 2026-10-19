# PoseDriverConnect / epic_pose_wrangler — 커스텀 포크 `[JUN]`

> Epic Games 공식 Maya 플러그인 **PoseDriverConnect(PoseWrangler)** 의 파이썬 소스를 포크해,
> **MetaHuman 이 아닌 아바타에도 RBF Pose Driver 프리셋을 임포트할 수 있도록** 직렬화 코드를 패치한 저장소입니다.

- **베이스**: Epic Games PoseDriverConnect — PoseWrangler `v2.5.0`, 직렬화 포맷 `1.2.0`
- **라이선스**: Apache License 2.0 (원본 유지, `LICENSE` 참조)
- **대상**: Maya 2018 ~ 2025 (Windows / Linux), Maya Python 3 + PySide2/PySide6

---

## 1. 이 저장소는 무엇인가

Epic 의 **PoseWrangler** 는 Maya 에서 **RBF(Radial Basis Function) Pose Driver** 를 오소링하고,
그 세팅을 JSON 으로 내보내 언리얼 엔진으로 넘기기 위한 공식 툴입니다.
관절이 굽을 때 헬퍼 조인트(무릎 back, thigh/calf twist corrective 등)를 자동으로 보정 이동시키는
**포즈 구동 변형(pose driven deformation)** 을 담당합니다.

이 저장소는 그 툴의 **파이썬 패키지 부분만** 담고 있는 포크입니다.

- **첫 커밋(`699e71e`)이 Epic 벤더 원본** 그대로입니다. 이후 커밋이 전부 제 수정분입니다.
  → 엔진 플러그인이 업데이트돼도 **`git log` 로 제 패치만 골라 재적용**할 수 있습니다.
- 저장소 루트는 모듈의 `python/` 폴더입니다. 솔버 노드 바이너리(`plug-ins/**/MayaUERBFPlugin.mll`)와
  `PoseDriverConnect.mod` 는 **Epic 배포본에서 그대로 가져와야 하며 이 저장소에는 포함되지 않습니다.**

---

## 2. 왜 포크했나 — 해결한 문제

**문제: MetaHuman 에서 오소링한 RBF 프리셋(JSON)을 다른 캐릭터 씬에 임포트하면 통째로 실패합니다.**

원인은 **델타 모드**(`metadata.serializer_params.delta = true`)로 저장된 파일의 역직렬화 경로에 있었습니다.
`epic_pose_wrangler/v2/model/serializers/serializer_v1_2_0.py` 의 `Serializer.deserialize()` 는

1. JSON 에 적힌 `driven_transforms` 목록이 **씬에 전부 존재한다고 전제**하고 현재 로컬 매트릭스를 수집하고
   (`utils.get_local_matrix_without_joint_orient`),
2. 포즈별 델타를 절대 매트릭스로 되돌릴 때 `current_driven_transforms[name]` 을 **무조건 참조**합니다.

즉 **헬퍼 조인트가 하나라도 빠진 커스텀 스켈레톤**에서는 임포트가 예외로 중단되어,
프리셋을 **부분적으로도** 적용할 수 없었습니다. MetaHuman 표준 스켈레톤 전체를 그대로 들고 있는 씬에서만 동작하는 셈입니다.

**해결: 원본 동작을 깨지 않는 최소 침습 패치 3단계** — 씬에 **실존하는 조인트에 대해서만** 솔버를 재구성합니다.

---

## 3. 수정 내역 (커밋 히스토리)

| 커밋 | 날짜 | 내용 |
|---|---|---|
| `699e71e` | 2026-05-28 | **first commit** — Epic 벤더 원본 (파이썬 소스 67개 파일, 9,004 라인) |
| `7279674` | 2026-05-28 | **Update serializer to ignore non-existent bones** — 존재하지 않는 driven 필터링 + 포즈 델타 루프 방어 |
| `6ef0f48` | 2026-05-28 | **update window name to [JUN]** — 커스텀 빌드 식별용 창 타이틀 태그 |
| `49a1e1a` | 2026-05-29 | **Skip solver creation when driven data is empty** — 빈 솔버 스킵, 디버그 print 정리, 실행 스니펫 + 회귀 확인용 샘플 JSON 추가 |

### 3-1. 존재하지 않는 driven 필터링 (`7279674`)

솔버 데이터를 읽는 시점에 `driven_transforms` 를 `cmds.objExists` 로 걸러 **씬에 실존하는 조인트만** 남깁니다.
→ 현재 포즈 매트릭스 수집 단계의 예외가 사라집니다.

```python
# serializer_v1_2_0.py :: deserialize()  — load_delta 분기 안쪽
for solver_name, solver_data in rbf_data.items():

    JUN__is_driven_empty[solver_name] = False
    JUN__dts = solver_data['driven_transforms']
    JUN__dts_new = []

    for JUN__d in JUN__dts:
        if cmds.objExists(JUN__d):
            JUN__dts_new.append(JUN__d)
    solver_data['driven_transforms'] = JUN__dts_new

    # 이 아래 원본 코드는 필터링된 목록만 보게 되므로 그대로 동작
    current_driven_transforms = {d: om.MMatrix(utils.get_local_matrix_without_joint_orient(d))
                                 for d in solver_data['driven_transforms']}
```

### 3-2. 포즈 델타 재계산 루프 방어 (`7279674`)

포즈별로 `delta × rest` 를 곱해 절대 매트릭스를 복원하는 루프에서도, 씬에 없는 driven 은 건너뛰어
`current_driven_transforms[name]` 의 `KeyError` 를 막습니다.

```python
for name, driven_transform in driven_transforms.items():
    if not cmds.objExists(name):      # ← 추가
        continue
    default_driven = current_driven_transforms[name]
    driven_transform = om.MMatrix(driven_transform)
    new_driven[name] = list(driven_transform * default_driven)
```

> **매트릭스 수학 메모** — `serialize()` 는 `pose × rest.inverse()` 로 델타를 저장하고,
> `deserialize()` 는 `delta × rest_현재씬` 으로 복원합니다.
> rest 포즈(첫 번째 포즈)만 **현재 씬 값으로 대체**되므로, 스켈레톤 프로포션이 달라도 델타가 재활용됩니다.
> 이 구조 덕분에 "있는 조인트만 골라 복원" 이 성립합니다.

### 3-3. 빈 솔버 스킵 (`49a1e1a`)

필터 결과 driven 이 **0 개가 된 솔버**를 표시해 두었다가 `RBFNode.create_from_data()` 단계에서 건너뛰고,
어떤 솔버를 무시했는지 로그로 남깁니다.
→ **구동 대상이 없는 껍데기 RBF 솔버 노드가 씬을 오염시키는 것**을 방지합니다.

```python
        if new_driven == {}:
            JUN__is_driven_empty[solver_name] = True
        pose_data['driven'] = new_driven

# ...

# Generate the solvers from the solver data
for solver_name, solver_data in rbf_data.items():
    if JUN__is_driven_empty[solver_name]:
        print(f"Ignore Solver : {solver_name}")
        continue
    api.RBFNode.create_from_data(solver_data)
```

### 3-4. 부가 정비

- **창 타이틀 태그** (`6ef0f48`) — 벤더 원본과 구분되도록 `Pose Wrangler [JUN] 2.5.0`
  (`v2/view/pose_wrangler_window.py`)
- **실행 스니펫** (`49a1e1a`) — 셸프에 그대로 붙일 수 있는 2줄짜리 `lunchCmd.py`
- **샘플 JSON** (`49a1e1a`) — `JUN__sample/sample_01.json`. MetaHuman 전신 프리셋(솔버 44개 —
  `calf_l/r`, `thigh_l/r`, `upperarm`, `lowerarm`, `clavicle`, `foot`, `hand`, 손가락 15쌍).
  예: `calf_l_UERBFSolver` = driver `calf_l` 1개 + driven 5개
  (`calf_kneeBack_l`, `calf_knee_l`, `calf_twistCor_02_l`, `thigh_twistCor_01/02_l`),
  포즈 5개(`default`, `calf_l_back_50/90/120/150`).
  **일부만 존재하는 스켈레톤에서 회귀 확인**하는 용도입니다.

---

## 4. 설치 및 실행

### 4-1. 드래그&드롭 설치 (권장, 2026-10-19~) — `.mod` 불필요

`python/__dragDrop_PoseWrangler.py` 를 **Maya 뷰포트로 드래그&드롭**하면 현재 셸프에 `PoseWrangler` 버튼이 생긴다.
제 다른 Maya 툴(`Maya_Python/JUN_All/tools/*/__dragDrop_<번호>.py`)과 같은 방식이다.

- 셸프 버튼 → `JUN__pose_wrangler_launch.run()`:
  ① `python/` 을 `sys.path` 에 넣고 ② 솔버 플러그인 `plug-ins/<windows|linux>/<마야 버전>/MayaUERBFPlugin.mll`
  을 **절대 경로로** `loadPlugin` ③ PoseWrangler 창을 띄운다. 경로는 런처 파일 위치에서 계산하므로
  **`PoseDriverConnect.mod` 도, 플러그인 경로 등록도 필요 없다.** 폴더(`plug-ins/` + `python/`)만 함께 있으면 어디에 둬도 된다.
- 드롭할 때 플러그인을 로드하고 **Auto load** 를 켠다 — 솔버 노드(`UERBFSolverNode`)가 든 씬을 툴보다 먼저
  열어도 노드가 unknown 이 되지 않는다.
- 이미 `.mod` 로 플러그인이 로드돼 있으면 그대로 쓴다(둘이 같이 있어도 충돌 없음).
- 같은 파일을 다시 드롭하면 옛 버튼을 지우고 새로 만든다. 아이콘은 `icon/PoseWrangler.png`.

### 4-2. 모듈(.mod) 설치 (Epic 원본 방식)

1. Epic 배포본의 `PoseDriverConnect` 모듈 폴더를 준비합니다 (`plug-ins/`, `PoseDriverConnect.mod` 포함).
2. 이 저장소를 모듈의 `python/` 폴더로 클론(또는 교체)합니다.

```
<maya>/modules/
├─ PoseDriverConnect.mod          ← Epic 원본
└─ PoseDriverConnect/
   ├─ plug-ins/                   ← Epic 원본 (MayaUERBFPlugin.mll, 2018~2025 / win64·linux)
   └─ python/                     ← 이 저장소
```

`.mod` 가 `MAYA_PLUG_IN_PATH` 와 `PYTHONPATH` 를 자동으로 잡아줍니다.

3. Maya 에서 실행 (셸프 버튼 / 스크립트 에디터):

```python
from epic_pose_wrangler import main
pose_wrangler = main.PoseWrangler()
```

4. 창 타이틀이 `Pose Wrangler [JUN] 2.5.0` 이면 이 포크가 로드된 것입니다.
5. RBF 프리셋 임포트: 툴 UI 의 **Import Solvers** (`v2/model/actions/io.py`) 또는

```python
pose_wrangler.api.deserialize_from_file(r"...\JUN__sample\sample_01.json")
```

임포트 시 스크립트 에디터에 `Ignore Solver : <이름>` 이 찍히면, **씬에 driven 조인트가 하나도 없어 건너뛴 솔버**입니다.

---

## 5. 저장소 구조

```
python/
├─ __dragDrop_PoseWrangler.py        ★ 뷰포트로 드롭 → 셸프 버튼 설치 (+ 플러그인 Auto load)
├─ JUN__pose_wrangler_launch.py      ★ 셸프 버튼 진입점 run() — 플러그인을 절대 경로로 로드 후 창
├─ icon/PoseWrangler.svg / .png      ★ 셸프 아이콘 (32px)
├─ lunchCmd.py                       ★ 셸프용 실행 스니펫 (.mod 설치 전제, 옛 방식)
├─ JUN__sample/
│  └─ sample_01.json                 ★ 회귀 확인용 MetaHuman 전신 RBF 프리셋 (솔버 44개)
├─ LICENSE                             Apache 2.0 (Epic 원본)
└─ epic_pose_wrangler/
   ├─ main.py                          진입점 (PoseWrangler)
   ├─ model/plugin_manager.py          솔버 플러그인 로드 + v1/v2 API 자동 선택
   ├─ resources/                       아이콘 / QSS / 스켈레톤 설정(metahuman.json, ue5.json) / 미러 매핑
   └─ v2/
      ├─ main.py                       UERBFAPI — 툴 본체 (VERSION = 2.5.0)
      ├─ model/
      │  ├─ api.py                     RBFNode / 솔버 노드 래퍼
      │  ├─ pose_blender.py            포즈 블렌딩
      │  ├─ mirror_mapping.py          좌우 미러
      │  ├─ utils.py                   get_local_matrix_without_joint_orient 등 매트릭스 유틸
      │  ├─ actions/                   Import/Export, 선택, Zero Pose 액션
      │  ├─ configs/                   스켈레톤 / 미러 매핑 설정 로더
      │  └─ serializers/
      │     ├─ serializer_v1_0_0.py
      │     ├─ serializer_v1_1_0.py
      │     └─ serializer_v1_2_0.py   ★★ 수정 지점 (delta 역직렬화)
      ├─ extensions/                   bake_poses, copy_paste_trs, generate_inbetweens, pose_exporter
      └─ view/                         PySide 창 / 위젯
```

`★` = 이 포크에서 추가, `★★` = 이 포크에서 수정한 핵심 파일.
**원본 대비 실제로 손댄 파이썬 파일은 `serializer_v1_2_0.py` 와 `pose_wrangler_window.py` 단 2개**입니다
(설치용 파일은 새로 더한 것뿐이라 벤더 코드는 그대로다).

> `.gitignore` 로 `docs/`(Sphinx 빌드 산출물)와 `epic_pose_wrangler/**/v1/`(구버전 API)은 추적하지 않습니다.
> `v1` 은 구형 `UE4RBFSolverNode` 노드가 있는 씬에서 `plugin_manager` 가 폴백하는 경로이므로,
> **로컬 모듈 폴더에는 Epic 원본의 `v1` 폴더를 그대로 두어야 합니다.**

---

## 6. 알려진 제약 / 주의사항

- **델타 모드 전용 패치입니다.** 필터링 로직은 `if load_delta:` 블록 안에 있습니다.
  `serializer_params.delta` 가 `false` 인(= 절대 매트릭스로 저장된) 파일을 임포트하면
  `JUN__is_driven_empty` 가 정의되지 않은 채 마지막 루프에 도달해 `NameError` 가 납니다.
  PoseWrangler 는 기본값이 `delta=True` 라 실사용 파일은 대부분 델타 모드이지만,
  **비델타 파일을 다룰 계획이라면 이 변수의 초기화를 `if` 블록 바깥으로 빼야 합니다.**
- **driven 이 부분적으로만 존재하는 솔버는 그대로 생성됩니다.** 5개 중 3개만 있으면 그 3개로 솔버가 만들어집니다
  (의도된 동작). 0개일 때만 스킵합니다.
- **`drivers` 는 필터링하지 않습니다.** 드라이버 조인트(예: `calf_l`)가 씬에 없으면 원본과 동일하게 실패합니다 —
  드라이버는 프리셋의 전제이므로 의도적으로 두었습니다.
- 패치 코드는 원본과 구분하기 위해 `JUN__` 접두사를 사용하고, 로그는 `LOG` 대신 `print` 를 씁니다.
  벤더 업데이트 시 **`JUN__` 로 grep 하면 패치 지점을 모두 찾을 수 있습니다.**

---

## 7. 결과

MetaHuman 에서 검증한 RBF 세팅을 **헬퍼 조인트 구성이 다른 비메타휴먼 아바타에 그대로 임포트**해,
**있는 조인트에 대해서만 솔버가 재구성**됩니다.
캐릭터마다 프리셋 JSON 을 손으로 잘라내거나 RBF 를 처음부터 다시 세팅할 필요가 없어졌습니다.

서드파티(엔진 벤더) 플러그인이라도 소스를 읽고 **델타 기반 포즈 데이터의 매트릭스 수학**
(rest 포즈 로컬 매트릭스 × 포즈 델타)을 이해하면 파이프라인에 맞게 고칠 수 있다는 사례입니다.
블랙박스로 두고 우회하는 대신 **원인 지점을 특정해 최소한으로 수정**했습니다.

**키워드**: PoseWrangler / PoseDriverConnect, RBF Pose Driver, 델타 직렬화(serializer), `cmds.objExists` 가드,
MMatrix 델타 복원, 서드파티 플러그인 포크·패치 관리, MetaHuman → 커스텀 아바타, Maya → Unreal

---

## 8. 원본 저작권

이 저장소의 `epic_pose_wrangler/` 코드는 **Copyright Epic Games, Inc. All Rights Reserved** 이며
Apache License 2.0 을 따릅니다. 이 포크는 위에 명시한 부분만 수정한 파생물입니다.
