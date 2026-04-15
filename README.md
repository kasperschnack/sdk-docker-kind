# Docker Workshop: Fra container til lokal Kubernetes

Velkommen til denne hands-on workshop, hvor du arbejder dig fra Docker-grundbegreber til at køre workloads i et lokalt Kubernetes-cluster.

Workshoppen er bygget til at gøre Kubernetes mindre abstrakt. Du starter med containere, bygger dine egne images, kører flere services sammen og flytter derefter den samme tankegang over i Kubernetes.

Du kommer til at:
- Forstå hvad containere er og hvorfor de er nyttige
- Bygge dine egne Docker-images
- Køre en app og en database sammen lokalt
- Oprette et lokalt cluster med `kind`
- Deploye din app med `Deployment` og `Service`
- Bruge `kubectl` til at se pods, logs og events

## Læringsmål

- Praktisk Docker
  - Installation og opsætning
  - Docker CLI
  - Volumes og netværk

- Docker Compose
  - Flere services i samme setup
  - En webapp og en database lokalt

- Lokal Kubernetes
  - Hvad et cluster egentlig er
  - `kind`, `kubectl` og container runtime
  - `Pod`, `Deployment`, `Service` og `Namespace`
  - Port-forwarding, logs og simpel fejlfinding

## Før du går i gang

Før du hopper ned i eksemplerne, skal vi sikre de praktiske forudsætninger, især på Windows-udviklerpc'er:

1. Installer WSL, hvis du arbejder på Windows.
2. Sørg for, at `git` er installeret inde i din WSL-distribution.
3. Klon dette repository lokalt, så du har workshop-materialet på din maskine.

Eksempel i WSL:

```bash
sudo apt update
sudo apt install -y git
git --version
git clone https://github.com/kasperschnack/aka-docker-local-k8s.git
cd aka-docker-local-k8s
```

Når det er på plads, kan du fortsætte med Docker-installation og derefter arbejde videre i eksemplerne som `examples/flask-demo`.
Hvis Docker ikke allerede er installeret, ligger installationsvejledningen i appendix nederst.

## Sektion 1: Containere

### Trin 1: Test at Docker virker

```bash
docker run hello-world
```

Hvis du ser `Hello from Docker!`, er du klar.

### Udforsk Docker CLI

```bash
docker pull nginx
docker images
docker run -d -p 8080:80 nginx
```

Besøg `http://localhost:8080`.

Stop og fjern containeren igen.
```bash
docker ps
docker stop <container-id>
docker rm <container-id>
```

## Byg din egen container

Vi tager udgangspunkt i det lille eksempel i [examples/flask-demo](examples/flask-demo).

Byg imaget:

```bash
cd examples/flask-demo
docker build -t flask-demo:local .
```

Kør containeren:

```bash
docker run --rm -p 5000:5000 flask-demo:local
```

Besøg `http://localhost:5000`.

Prøv også selv at ændre appen. Åbn `app.py` og ret teksten i `message`, for eksempel fra `Hej fra Flask i lokal Kubernetes` til noget andet.

Når du har ændret filen, skal du bygge imaget igen og starte containeren igen for at se ændringen:

```bash
docker build -t flask-demo:local .
docker run --rm -p 5000:5000 flask-demo:local
```

Verificer bagefter i browseren på `http://localhost:5000`, eller med:

```bash
curl http://localhost:5000
```

Hvis du stadig ser den gamle tekst, kører du sandsynligvis stadig den gamle container eller det gamle image.

### Hvad er der i Dockerfile'en?

- Vi starter fra `python:3.11-slim`
- Vi kopierer `requirements.txt` først for bedre caching
- Vi installerer Flask
- Vi kopierer resten af appen ind bagefter

## Volumes og bind mounts

Containere er som udgangspunkt stateless. Hvis du vil gemme data mellem kørsler, skal du gemme dem uden for containerens eget filsystem.

Volume eksempel:

```bash
docker run -v minvolume:/data busybox sh -c "echo 'Hej fra mit volume' > /data/hilsen.txt"
docker run -v minvolume:/data busybox cat /data/hilsen.txt
```

Bind mount eksempel:

```bash
docker run -v $(pwd)/output:/data busybox sh -c "echo 'Hej fra bind mount' > /data/hilsen.txt"
cat output/hilsen.txt
```

Et simpelt udviklingseksempel med bind mount:

```bash
cd examples/flask-demo
docker run --rm -p 5000:5000 -v $(pwd):/app \
  -e FLASK_APP=app.py \
  flask-demo:local flask run --host=0.0.0.0 --port=5000 --debug
```

Nu bruger containeren filerne fra din lokale mappe, og Flask genstarter automatisk ved ændringer. Ret teksten i `message` i `app.py`, gem filen og genindlæs `http://localhost:5000`.

Det er nyttigt i udvikling, fordi du kan teste små ændringer hurtigt. Når du bygger image, tester du det, der faktisk bliver pakket. Når du bruger bind mount, tester du hurtigere lokalt.

## Docker Compose med web og database

Der ligger et eksempel i [examples/flask-postgres](examples/flask-postgres).

Kør det lokalt:

```bash
cd examples/flask-postgres
docker compose up --build
```

Besøg `http://localhost:5000`.

Det setup er vigtigt, fordi det ligner noget, du senere vil splitte op i Kubernetes-ressourcer.

## Sektion 2: Lokal Kubernetes

Nu skifter vi perspektiv. I stedet for at sende vores image til en cloud-provider bruger vi et lokalt cluster, så du kan lære de samme grundbegreber uden at betale for noget eller rydde op i cloud-ressourcer bagefter.

## Hvorfor `kind`?

`kind` betyder Kubernetes IN Docker. Det er et let setup til lokal læring:

- Hurtigt at oprette og slette
- Kører på din egen maskine
- Godt til at lære `kubectl` og manifests
- Ingen Azure-konto eller registry er nødvendig

Hvis målet er at forstå begreberne, er `kind` et bedre første skridt end at hoppe direkte i managed Kubernetes.

## Trin 2: Installer værktøjer

Du skal bruge:

- Docker
- `kubectl`
- `kind`

`kubectl`:

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

`kind`:

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

Tjek versioner:

```bash
docker --version
kubectl version --client
kind version
```

## Trin 3: Opret et cluster

```bash
kind create cluster --name workshop
```

Tjek at clusteret findes:

```bash
kind get clusters
kubectl cluster-info
kubectl get nodes
```

## Trin 4: Byg et image og load det ind i clusteret

Vi bruger samme Flask-app som før.

```bash
cd examples/flask-demo
docker build -t flask-demo:local .
kind load docker-image flask-demo:local --name workshop
```

`kind` kan ikke automatisk se alle images fra din lokale Docker daemon som et normalt registry ville kunne. Derfor loader vi imaget direkte ind i clusteret.

## Trin 5: Deploy appen i Kubernetes

Der ligger manifests i [examples/flask-demo/k8s](examples/flask-demo/k8s).

Anvend dem:

```bash
kubectl apply -f examples/flask-demo/k8s
```

Se hvad der bliver oprettet:

```bash
kubectl get namespaces
kubectl get deployments -n workshop
kubectl get pods -n workshop
kubectl get services -n workshop
```

## Trin 6: Gør appen tilgængelig

I et lokalt cluster er `port-forward` den enkleste vej:

```bash
kubectl port-forward -n workshop service/flask-demo 5000:5000
```

Besøg `http://localhost:5000`.

## Hvad er forskellen på de vigtigste ressourcer?

- `Pod`: den konkrete instans, der kører dine containere
- `Deployment`: beskriver hvordan pods skal oprettes og holdes i live
- `Service`: giver en stabil netværksadresse til en eller flere pods
- `Namespace`: en logisk opdeling i clusteret

En god mental model er:

- Docker kører containere
- Compose kører flere containere sammen
- Kubernetes holder workloads kørende og giver dig en deklarativ model

## Trin 7: Fejlfinding med `kubectl`

De vigtigste kommandoer i starten er:

```bash
kubectl get pods -A
kubectl describe pod <pod-navn> -n workshop
kubectl logs deployment/flask-demo -n workshop
kubectl get events -n workshop --sort-by=.lastTimestamp
```

Hvis en pod ikke starter, er `describe` og `logs` som regel det rigtige første sted at kigge.

## Trin 8: Skalering

```bash
kubectl scale deployment flask-demo --replicas=3 -n workshop
kubectl get pods -n workshop
```

Nu kan du se, at Kubernetes holder tre ens pods kørende bag den samme service.

## Trin 9: Ryd op

Slet workloaden:

```bash
kubectl delete -f examples/flask-demo/k8s
```

Slet clusteret:

```bash
kind delete cluster --name workshop
```

## Ekstra øvelse: Fra Compose til Kubernetes

I [examples/flask-postgres/k8s](examples/flask-postgres/k8s) ligger et bevidst simpelt eksempel på den samme app som i Compose-udgaven.

Det er ikke et produktionssetup. Det er et læringssetup.

Ting du kan kigge efter:

- Hvordan `db` i Compose bliver til en `Service`
- Hvordan miljøvariabler flytter over i manifests
- Hvorfor persistence hurtigt bliver et større emne i Kubernetes

## Tjekliste

### Docker
- [ ] Køre `hello-world`
- [ ] Bygge et image lokalt
- [ ] Starte en Flask-app i Docker
- [ ] Forstå forskellen på volume og bind mount
- [ ] Køre flere services med Compose

### Kubernetes lokalt
- [ ] Installere `kubectl` og `kind`
- [ ] Oprette et lokalt cluster
- [ ] Loade et image ind i `kind`
- [ ] Deploye med `kubectl apply`
- [ ] Bruge `port-forward`
- [ ] Læse logs og events
- [ ] Skalere en deployment
- [ ] Slette clusteret igen

## Hvad blev ikke dækket?

- Ingress controllers
- Persistent volumes i dybden
- Helm charts
- ConfigMaps og Secrets i mere realistiske setups
- Health checks og probes
- CI/CD
- Managed Kubernetes som AKS, EKS eller GKE

Det er bevidst. Først giver det mening at forstå de lokale grundbegreber.

Hvis du senere vil videre, er den naturlige progression:

1. Lokal Docker
2. Lokal Kubernetes med `kind`
3. Mere realistiske manifests
4. Helm
5. Managed Kubernetes

## Sektion 3: Bonus - fra `kind` til vores egen Talos-platform

`kind` er godt til at lære Kubernetes-begreberne hurtigt. Vores egen lokale platform er noget andet. Den handler ikke kun om at køre pods, men også om at bygge og drive selve clusteret.

Det er den vigtigste forskel:

- I `kind` får du et færdigt cluster med det samme
- I Talos-setuppet bygger vi clusteret bevidst op fra bunden

Denne del er inspireret af vores setup i `DevOps-kubernetes-master`.

## Den mentale overgang

Hvis du har lavet øvelserne ovenfor, kender du allerede de vigtigste Kubernetes-objekter:

- `Deployment`
- `Pod`
- `Service`
- `Namespace`

I vores Talos-setup arbejder vi et niveau under det:

- Hvordan control planes bliver oprettet
- Hvordan worker nodes bliver oprettet
- Hvordan clusteret bliver bootstrapped
- Hvordan API endpoint og netværk bliver gjort stabile
- Hvordan basis-komponenter som Cilium bliver installeret

Kort sagt:

- Workshop del 1 og 2 handler om workloads i Kubernetes
- Bonusdelen handler om selve Kubernetes-platformen

## Hvordan vores setup er bygget op

Det overordnede flow ligger i `ansible/playbooks/cluster.yml` i `DevOps-kubernetes-master`.

Her er ideen:

1. Talos-infrastruktur bliver provisioneret
2. Talos bliver opgraderet, hvis det er nødvendigt
3. Kubernetes-services bliver deployet bagefter

Det er en vigtig opdeling, fordi den skiller platform fra workloads.

- Platform er fx noder, bootstrap, netværk og kubeconfig
- Workloads er fx services, controllers og applikationer

## Hvad sker der i praksis?

Provisioneringsflowet ligger i `ansible/playbooks/talos/deploy-infra.yml` i `DevOps-kubernetes-master`.

Det kan læses som fire hovedtrin:

1. Der laves nye Talos-secrets til personlige clusters
2. Control plane-noder bliver oprettet
3. Clusteret bliver bootstrapped
4. Worker-noder og basis-services bliver gjort klar

Det er meget tættere på et rigtigt cluster-livscyklusforløb end `kind`.

## Control plane og worker nodes

I workshoppen så du pods og deployments. I Talos-setuppet skal vi først have maskinerne.

## Appendix: Installer Docker

Hvis du mangler Docker på din maskine, kan du bruge et af disse spor.

### Windows

På Windows er Docker Desktop den nemmeste vej.

- Download Docker Desktop: <https://www.docker.com/products/docker-desktop/>
- Følg installationsguiden for Windows: <https://docs.docker.com/desktop/setup/install/windows-install/>
- I denne workshop tager vi udgangspunkt i Docker Desktop på Windows sammen med WSL

### Ubuntu

Et simpelt Ubuntu-eksempel:

```bash
sudo apt update
sudo apt install docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Log ud og ind igen, hvis du har kørt `usermod`.

Control plane provisioning sker i `ansible/roles/hypervisor/talos-vm/control-plane/tasks/main.yml` i `DevOps-kubernetes-master`.

Der sker blandt andet dette:

- Der genereres Talos machineconfig med `talosctl gen config`
- Der patches netværk og hostname ind
- Konfigurationen bliver lagt ind som VM boot-parameter
- VM'en bliver oprettet i vSphere

Worker provisioning i `ansible/roles/hypervisor/talos-vm/worker-node/tasks/main.yml` i `DevOps-kubernetes-master` følger samme mønster, men med worker-konfiguration.

Det er den konkrete version af:

- `kind`: "lav et cluster"
- Talos-platform: "byg de maskiner clusteret kører på"

## Bootstrap: hvornår bliver det til et rigtigt cluster?

Det step ligger i `ansible/roles/talos/bootstrap/tasks/main.yml` i `DevOps-kubernetes-master`.

Her bliver en control plane node brugt til at bootstrappe clusteret, og de andre control planes bliver bagefter koblet på.

Det er et godt sted at forbinde teori og praksis:

- Kubernetes API findes ikke rigtigt før bootstrap
- `kubectl` giver først mening, når control plane er oppe
- Et HA-control-plane er ikke bare "flere VM'er", men en samlet kontrolflade

## VIP og stabil API-adgang

I `kind` tænker man ikke så meget over API-endpointet. I et rigtigt setup betyder det mere.

I `ansible/roles/talos/configure-vip/tasks/main.yml` i `DevOps-kubernetes-master` bliver control plane-konfigurationen patched, så API'et peger på en virtuel IP.

Det løser et konkret problem:

- Du vil ikke binde din kubeconfig og dine tools til en enkelt control plane node
- Du vil have et stabilt endpoint selv hvis en node forsvinder

Det er samme slags stabilitetsprincip, som en Kubernetes `Service` giver workloads, bare på clusterets egen kontrolflade.

## CNI og netværk: hvorfor Cilium betyder noget

I workshoppen brugte du `Service` og port-forward uden at skulle tænke særligt over det underliggende netværk. I vores platform er det en bevidst del af setup'et.

I `ansible/roles/talos/cilium/tasks/main.yml` i `DevOps-kubernetes-master` bliver Talos patched, så standard-CNI og `kube-proxy` ikke bruges, og derefter bliver Cilium installeret.

Det er vigtigt af to grunde:

- Pods skal kunne tale sammen
- Services skal kunne rout'es stabilt

Det er med andre ord den del, der gør, at dine workloads faktisk kan opføre sig som et cluster og ikke bare som isolerede containere.

## `kubeconfig` og `talosconfig`

I `kind` får du meget foræret. I Talos-setuppet er klientkonfiguration en tydeligere del af flowet.

`Justfile` i `DevOps-kubernetes-master` viser det ret godt:

- `just kubeconfig ...` genererer adgang til Kubernetes
- `just deploy-personal <initialer>` kører hele det personlige clusterflow
- `just reset-personal <initialer>` rydder lokal Talos- og kubeconfig-state op

Det er nyttigt at skelne mellem:

- `kubeconfig`: hvordan du snakker med Kubernetes API
- `talosconfig`: hvordan du administrerer selve Talos-noderne

Den skelnen findes ikke i den simple `kind`-øvelse, men den er vigtig i et mere realistisk setup.

## Hvordan bonusdelen hænger sammen med workshoppen

Her er den korte mapping:

- `docker run` lærer dig, hvad en container er
- `docker compose` lærer dig, hvad flere services er
- `kind` lærer dig de vigtigste Kubernetes-objekter
- Talos-setuppet lærer dig, hvordan clusteret bag objekterne bliver skabt og drevet

Det vil sige:

- Sektion 1: containere
- Sektion 2: workloads i Kubernetes
- Sektion 3: platformen der kører Kubernetes

## Hvis du vil koble det til vores egen hverdag

Når du arbejder i det rigtige setup, kan du tænke sådan her:

- Hvis problemet handler om pods, services, namespaces eller logs, er du i workload-laget
- Hvis problemet handler om node bootstrap, Talos config, VIP eller Cilium, er du i platform-laget

Den opdeling gør debugging og ansvar meget mere overskueligt.

## Forslag til videre bonus-øvelser

1. Læs `ansible/playbooks/talos/deploy-infra.yml` i `DevOps-kubernetes-master` og identificer, hvor control plane, bootstrap og worker provisioning sker.
2. Læs `ansible/playbooks/cluster.yml` i `DevOps-kubernetes-master` og forklar forskellen på platform deployment og service deployment.
3. Læs `ansible/roles/talos/cilium/tasks/main.yml` i `DevOps-kubernetes-master` og forklar, hvorfor netværk ikke bare er en detalje i Kubernetes.
4. Læs `ansible/roles/talos/bootstrap/tasks/main.yml` i `DevOps-kubernetes-master` og forklar, hvorfor bootstrap kun må ske fra en control plane node ad gangen.
