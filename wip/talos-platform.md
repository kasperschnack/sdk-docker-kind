# Work in Progress: Fra `kind` til vores egen Talos-platform

Det her materiale er under udvikling og er ikke en del af workshoppens primære flow endnu.

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
