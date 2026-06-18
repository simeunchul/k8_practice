# k8s/local — Phase 2 (경량): 오퍼레이터 없이 K8s 위에 파이프라인 배포·운영

Strimzi/Spark/Helm 없이 **kind 로컬 클러스터**에 단일노드 Kafka + producer + consumer를
평범한 `Deployment`/`Service`로 올려, **"K8s 위에서 서비스를 개발·배포·운영"** 을 가장 빠르고
확실하게 검증하는 경로다. (전체 Strimzi+Spark 경로는 상위 [k8s/README.md](../README.md) 참고 — 그쪽은 코드 초안.)

> **상태: ✅ 로컬 kind 클러스터에서 배포·운영 실행·검증 완료** (아래 "실행 증거" 참고).
> 단일 노드·ephemeral 저장소·복제계수 1의 **토이** 구성이다(운영용 아님).

## 구성

```
namespace(econ)
  ├─ Deployment/Service  kafka        (apache/kafka:3.9.0, KRaft 단일노드, ClusterIP kafka:9092)
  ├─ Deployment          econ-producer (mock 경제지표를 econ.indicators 로 5s 간격 발행)
  └─ Deployment          econ-consumer (econ.indicators 소비 + 오프셋 수동 커밋)
```

파일: [`kind-cluster.yaml`](kind-cluster.yaml) · [`kafka.yaml`](kafka.yaml) · [`producer.yaml`](producer.yaml) · [`consumer.yaml`](consumer.yaml) · [`run-local-kind.sh`](run-local-kind.sh)

## 사전 준비 (Windows 기준)

- **Docker Desktop** 실행 중
- **kubectl** (Docker Desktop에 포함)
- **kind** — 단일 바이너리. 설치:
  ```bash
  # PowerShell 또는 git-bash
  curl -fL -o "$HOME/bin/kind.exe" https://github.com/kubernetes-sigs/kind/releases/download/v0.32.0/kind-windows-amd64
  export PATH="$HOME/bin:$PATH"   # kind.exe 가 있는 곳을 PATH에
  kind version
  ```

## 한 번에 실행

```bash
bash k8s/local/run-local-kind.sh
```

스크립트가 하는 일: kind 클러스터 생성 → producer/consumer 이미지 빌드 → `kind load` 로 노드에 주입
(레지스트리 불필요) → `namespace/kafka/producer/consumer` 적용 → 각 Deployment `rollout status` 대기 → 상태 출력.

## 동작 확인 (배포)

```bash
kubectl get pods,svc,deploy -n econ
# 발행 로그
kubectl -n econ logs -l app=econ-producer --tail=10
# 소비 + 오프셋 커밋 로그
kubectl -n econ logs -l app=econ-consumer --tail=12
```

## 운영(operate) 연습

```bash
kubectl -n econ scale deploy/econ-consumer --replicas=2      # 스케일 아웃 (그룹 내 파티션 분산)
kubectl -n econ rollout restart deploy/econ-producer         # 무중단 롤아웃 재시작
kubectl -n econ rollout status  deploy/econ-producer
kubectl -n econ describe pod -l app=kafka                    # 이벤트·probe 상태
```

## 정리

```bash
kind delete cluster --name econ
```

---

## 실행 증거 (2026-06-17, 로컬 kind v0.32.0 / node v1.36.1)

```text
# 배포 상태
$ kubectl get pods -n econ
NAME                             READY   STATUS    RESTARTS   AGE
econ-consumer-664889d8d-j7fwx    1/1     Running   0          79s
econ-producer-86f4b84dc9-zsfql   1/1     Running   0          47s
kafka-76fc49bdd4-rw4kn           1/1     Running   0          2m37s

# producer — econ.indicators 로 발행 (offset 연속 증가)
$ kubectl -n econ logs econ-producer-86f4b84dc9-zsfql --tail=5
  ✓ econ.indicators[0] @ offset 151
  ✓ econ.indicators[0] @ offset 152
  ✓ econ.indicators[0] @ offset 153
  ✓ econ.indicators[0] @ offset 154
  ✓ econ.indicators[0] @ offset 155

# consumer — 소비 + 오프셋 수동 커밋 (group=econ-consumer-1)
$ kubectl -n econ logs econ-consumer-664889d8d-j7fwx --tail=8
  [0@176] 기준금리=3.559
  [0@177] 원달러환율=1383.0804
  [0@178] 코스피=2608.4084
  [0@179] 소비자물가지수=113.0033
  [0@180] 기준금리=3.5792
  [0@181] 원달러환율=1373.7034
  [0@182] 코스피=2606.1981
  [0@183] 소비자물가지수=112.5254

# operate — consumer 스케일 아웃 / producer 롤아웃 재시작 확인
$ kubectl -n econ scale deploy/econ-consumer --replicas=2 && kubectl get pods -n econ -l app=econ-consumer
econ-consumer-6c8d5dcd8-h8pgg    1/1     Running       0   34s
econ-consumer-6c8d5dcd8-kfbn7    1/1     Running       0    1s
$ kubectl -n econ rollout restart deploy/econ-producer   # → 새 ReplicaSet 으로 무중단 교체
deployment.apps/econ-producer restarted

# self-healing — consumer 파드 강제 삭제 → Deployment 가 1s 만에 자동 재생성
$ kubectl -n econ delete pod econ-consumer-664889d8d-j7fwx --wait=false
pod "econ-consumer-664889d8d-j7fwx" deleted
$ kubectl -n econ get pods -l app=econ-consumer
econ-consumer-664889d8d-j7fwx   1/1   Terminating   0   13m
econ-consumer-664889d8d-l6ss2   1/1   Running       0    1s   # ← 자동 재생성

# rolling update 실패 → 무중단 + rollout undo 로 복구
$ kubectl -n econ set image deploy/econ-producer producer=econ-producer:does-not-exist
$ kubectl -n econ get pods -l app=econ-producer
econ-producer-5699d977c-mcsvg    0/1   ErrImagePull   0   40s   # ← 새 버전 실패
econ-producer-86f4b84dc9-zsfql   1/1   Running        0   14m   # ← 기존 버전 무중단 유지
$ kubectl -n econ rollout undo deploy/econ-producer
deployment.apps/econ-producer rolled back   # ← 정상 버전으로 즉시 복구
```

## 처음 띄울 때 만난 함정 (실제 디버깅 기록)

1. **Kafka readiness probe timeout** — `kafka-topics.sh`(JVM CLI)는 cpu 제한 파드에서 cold-start 가
   10초를 넘겨 readiness probe 가 계속 실패 → 파드가 영원히 NotReady. 브로커 자체는 정상 기동이었음
   (`Kafka Server started`). → readiness 를 **`tcpSocket: 9092`** 로 교체해 해결.
2. **컨테이너 로그가 안 보임** — Python `print()` 가 컨테이너(비 TTY)에서 block-buffered 라 stdout 이
   flush 되지 않음 → `kubectl logs` 가 빈 출력. → Deployment 에 **`PYTHONUNBUFFERED=1`** 추가로 해결.
3. **로컬 이미지 주입** — kind 는 호스트 도커 이미지를 자동으로 못 봄 → `kind load docker-image` 로
   노드에 적재하고 `imagePullPolicy: IfNotPresent` 로 로컬 이미지를 쓰게 함(레지스트리 불필요).
