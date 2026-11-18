# 워프레임 강철의 길 보이드 범람 → Discord 알림

GitHub Actions가 **5분마다** WarframeStat의 PC 균열 API를 조회해, **투불 광장(자리만) / 보이드 범람 / 강철의 길 (Lv. 150–155)** 미션이 생기면 Discord Webhook에 알림을 보냅니다. 동일 균열 ID는 알림을 한 번만 전송합니다.

## 1. GitHub 저장소 생성

1. GitHub에서 **New repository**를 누릅니다. 예: `warframe-fissure-alert` (Public 또는 Private).
2. 이 ZIP의 **내용물**을 저장소 **기본 브랜치**(보통 `main`)에 그대로 업로드합니다. `.github/workflows/warframe-alert.yml` 경로와 숨김 폴더 이름을 유지하세요. ZIP 자체를 업로드하면 동작하지 않습니다.
3. 기본 브랜치에서 Actions가 활성화되어 있는지 확인합니다.

## 2. Discord 웹훅 만들기

1. 알림을 받을 Discord 텍스트 채널 → **채널 편집 → 연동(Integrations) → 웹후크(Webhooks)**.
2. 웹후크를 새로 만들고 URL을 복사합니다.
3. 이 URL은 비밀번호처럼 다루세요. 코드나 README에 붙여 넣지 않습니다.

## 3. GitHub Secret 추가

저장소 → **Settings → Secrets and variables → Actions → New repository secret**:

- **Name:** `DISCORD_WEBHOOK_URL`
- **Secret:** 복사한 Discord 웹훅 URL

## 4. 상태 파일 쓰기 권한

저장소 → **Settings → Actions → General → Workflow permissions**에서 **Read and write permissions**를 선택하고 Save 합니다. 조직 정책이나 브랜치 보호 규칙이 GitHub Actions의 push를 막으면 상태 저장이 실패해 중복 알림이 날 수 있습니다. 처음에는 브랜치 보호가 없는 별도 저장소를 권장합니다.

## 5. 수동 테스트

저장소 → **Actions → Warframe Tuvul Fissure Alert → Run workflow** → `test_notification` **true** → Run workflow.

Discord에 `✅ 워프레임 균열 알림 웹훅 연결 테스트 성공!`이 오면 웹훅 연결은 정상입니다. 이 테스트는 중복 상태를 변경하지 않습니다.

이후 한 번 더 **Run workflow**에서 `test_notification` **false**로 실행하면 현재 실제 균열을 조회합니다. 대상 미션이 활성화 중이면 즉시 알림이 옵니다. 활성화 중이 아니면 아무 메시지도 보내지 않습니다.

## 동작과 중복 방지

- 검사 API: `https://api.warframestat.us/pc/fissures` (PC 글로벌 상태)
- 필터: `isHard == true`, `isStorm != true`, `node == 'Tuvul Commons (Zariman)'`, `missionType == 'Void Cascade'`
- 균열마다 고유 `id`를 `notified_fissures.json`에 기록합니다.
- GitHub Actions가 알림 후 해당 파일을 저장소에 자동 커밋하므로 다음 실행에서도 중복을 막습니다.
- 만료된 균열의 ID는 자동 정리합니다. 새로 생성된 같은 위치의 균열은 새로운 ID이므로 새로 알림을 보냅니다.
- `concurrency`를 통해 중복 실행을 줄입니다.

**주의:** Discord 전송은 성공했지만 GitHub 상태 파일 커밋/푸시가 실패하는 극단적인 경우에는 다음 실행에서 중복 알림이 발생할 수 있습니다. GitHub Actions에서 Discord와 Git 상태를 하나의 원자적 트랜잭션으로 처리할 수 없으므로 100% exactly-once 전송은 보장하지 않습니다.

## 알아둘 점

- GitHub Actions의 `schedule` 최소 간격은 **5분**이며 실행 시작이 지연되거나 일부 실행이 누락될 수도 있습니다. 짧게 등장했다 사라지는 균열은 놓칠 가능성이 있습니다.
- 일정 기간 활동이 없는 **공개 저장소**는 GitHub에서 스케줄 실행을 비활성화할 수 있습니다. Actions 탭에서 다시 활성화하세요.
- `GITHUB_TOKEN`으로 만든 상태 커밋은 일반적으로 새 `push` 워크플로를 추가 실행하지 않습니다.
- 플랫폼이 PC가 아닌 경우 `API_URL`을 플랫폼에 맞게 조정해야 합니다.
- API의 영문 노드/미션 이름이 달라질 경우 `warframe_alert.py`의 `target()`을 수정해야 합니다.
- 웹훅 권한과 주소가 바뀌면 Secret을 갱신해야 합니다.

## 로컬 테스트 (선택)

```bash
python -m unittest discover -s tests -v
```

별도 pip 패키지 설치가 필요하지 않습니다.


## 한국시간 시작 및 종료 표시

디스코드 알림에 API의 `activation`(등장 시간)과 `expiry`(종료 시간)를 `Asia/Seoul` 기준으로 변환한 `YYYY-MM-DD HH:MM:SS KST` 형식으로 표시합니다. Discord 상대 시각으로 남은 시간도 함께 표시합니다. 이 시각은 GitHub Actions에서 알림을 감지한 시각이 아니라 API에 기록된 미션 시작/종료 시각입니다. 이전에 업로드한 프로젝트를 사용한다면 `warframe_alert.py`만 교체해도 되고, 테스트를 갱신하려면 `tests/test_alert.py`도 교체하세요.
