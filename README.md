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

Prøv også selv at ændre appen. Åbn `app.py` og ret teksten i `message`, for eksempel fra `Hej fra Flask` til noget andet.

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

Her opretter Docker et navngivet volume med navnet `minvolume`, hvis det ikke allerede findes. Data bliver gemt på værtsmaskinen i Dockers egen storage og ikke inde i containerens filsystem. Derfor kan den anden container læse den samme fil igen, selv om den første container er væk.

Bind mount eksempel:

```bash
docker run -v $(pwd)/output:/data busybox sh -c "echo 'Hej fra bind mount' > /data/hilsen.txt"
cat output/hilsen.txt
```

Et simpelt udviklingseksempel med bind mount:

```bash
docker run --rm -p 5000:5000 -v $(pwd):/app \
  -e FLASK_APP=app.py \
  flask-demo:local flask run --host=0.0.0.0 --port=5000 --debug
```

Nu bruger containeren filerne fra din lokale mappe, og Flask genstarter automatisk ved ændringer. Ret teksten i `message` i `app.py`, gem filen og genindlæs `http://localhost:5000`.

Det er nyttigt i udvikling, fordi du kan teste små ændringer hurtigt. Når du bygger image, tester du det, der faktisk bliver pakket. Når du bruger bind mount, tester du hurtigere lokalt.

## Docker Compose med web og database

Der ligger et eksempel i [examples/flask-postgres](examples/flask-postgres).

Nu skal vi til at prøve kræfter med `docker compose`. Det bruges til at starte flere containere som ét samlet setup, for eksempel en webapp og en database, med netværk og miljøvariabler sat op på forhånd.

Hvis du arbejder i Ubuntu eller WSL, kommer `docker compose` ikke altid med som en del af det øvrige Docker-setup. Hvis kommandoen ikke findes, så følg den officielle installationsguide her:

<https://docs.docker.com/compose/install/linux/#install-using-the-repository>

Kør det lokalt:

```bash
cd ../flask-postgres
docker compose up --build
```

Her sker der i praksis dette:

- `web`-servicen bliver bygget fra `examples/flask-postgres/app`
- `db`-servicen starter en PostgreSQL-container fra `postgres:15`
- `web` får forbindelse til databasen via hostnavnet `db`, fordi Compose opretter et internt netværk mellem services
- `depends_on` sørger for, at databasen bliver startet før `web`
- Postgres-data bliver gemt i volume'et `pgdata`, så de ikke forsvinder, bare fordi containeren bliver genstartet

Besøg `http://localhost:5000`.

Det setup er vigtigt, fordi det ligner noget, du senere vil splitte op i Kubernetes-ressourcer.

## Sektion 2: Lokal Kubernetes

Nu skifter vi perspektiv. I stedet for at arbejde i vores ITm8-setup bruger vi her et lokalt cluster, så du kan lære de samme grundbegreber på din egen maskine. Du kan stadig tænke på det som et alternativ til at køre i skyen, men i vores kontekst er det lokale setup først og fremmest en proxy for miljøet på ITm8s infrastruktur.

## Hvorfor `kind`?

`kind` betyder Kubernetes IN Docker. Det er et let setup til lokal læring:

- Hurtigt at oprette og slette
- Kører på din egen maskine
- Godt til at lære `kubectl` og manifests
- Ingen adgang til ITm8-infrastruktur eller eksternt registry er nødvendig

Hvis målet er at forstå begreberne, er `kind` et bedre første skridt end at hoppe direkte ind i det fulde setup på ITm8s infrastruktur.

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

`kind` kan ikke automatisk se alle images fra din lokale Docker daemon. Derfor loader vi imaget direkte ind i clusteret i stedet for at publicere det til et registry og hente det derfra.

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
- Kubernetes holder workloads kørende og giver dig en deklarativ model, uanset om clusteret kører lokalt eller på ITm8s infrastruktur

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

## Appendix: Installer Docker

Hvis du mangler Docker på din maskine, kan du bruge et af disse spor.

### Windows

På Windows er Docker Desktop den nemmeste vej.

- Download Docker Desktop: <https://www.docker.com/products/docker-desktop/>
- Følg installationsguiden for Windows: <https://docs.docker.com/desktop/setup/install/windows-install/>
- I denne workshop tager vi udgangspunkt i Docker Desktop på Windows sammen med WSL
- Docker Compose følger normalt med Docker Desktop og kan tjekkes med `docker compose version`

### Ubuntu

Et simpelt Ubuntu-eksempel:

```bash
sudo apt update
sudo apt install docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Log ud og ind igen, hvis du har kørt `usermod`.
