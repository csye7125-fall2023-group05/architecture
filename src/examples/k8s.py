from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom

from diagrams.aws.compute import Compute
from diagrams.gcp.compute import ComputeEngine, GKE
from diagrams.gcp.devtools import ContainerRegistry
from diagrams.gcp.network import VirtualPrivateCloud

from diagrams.k8s.infra import Master, Node
from diagrams.k8s.compute import Pod, Deploy, RS, STS, Cronjob, Job
from diagrams.k8s.storage import PV, PVC, SC
from diagrams.k8s.network import SVC
from diagrams.k8s.podconfig import CM, Secret
from diagrams.k8s.clusterconfig import HPA
from diagrams.k8s.ecosystem import Helm
from diagrams.k8s.others import CRD

from diagrams.onprem.ci import GithubActions, Jenkins
from diagrams.onprem.client import Client, Users, User
from diagrams.onprem.queue import  Kafka
from diagrams.onprem.network import Zookeeper, Envoy, Istio
from diagrams.onprem.compute import Server
from diagrams.onprem.container import Docker
from diagrams.onprem.iac import Terraform
from diagrams.onprem.database import Postgresql
from diagrams.onprem.logging import Fluentbit
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.vcs import Github

with Diagram("Kubernetes Architecture", show=False, outformat="svg"):
    source = User("Developer")
    registry = ContainerRegistry("Container Registry")
    tf = Terraform("IaC")

    # developer IaC deployment
    source >> Edge(label="deploy", color="purple", style="dashed") >> tf

    # endpoint access by edn users
    with Cluster("End Users"):
        users = Users("Users")

    # GitHub VCS
    with Cluster("Github"):
        github = Github("GitHub")
        ghActions = GithubActions("CI")
        webHookCustom = Custom("Webhook" ,"src/examples/my_resources/webhook.svg")

    # CI/CD Infra
    with Cluster("AWS Hosted Jenkins"):
        compute_instance = Compute("Jenkins Server")
        packer = Custom("Packer", "src/examples/my_resources/packer.svg")
        with Cluster("AMI"):
            jenkins = Jenkins("Jenkins")
            docker = Docker("Container Runtime")
            ami = [jenkins, docker]

        tf >> Edge(color="purple", style="bold") >> compute_instance

        source >> Edge(label="commit", color="olive", style="bold") >> github >> Edge(label="CI") >> ghActions >> Edge(label="triggers") >> webHookCustom >> compute_instance << Edge(color="red", style="dotted") << packer - Edge(color="darkblue", style="dashed") - jenkins >> Edge(label="buildx") >> docker >> Edge(label="push") >> registry

    # GCP -> GKE Infra
    with Cluster("Google Cloud Platform"):
        with Cluster("VPC"):
            vpc = VirtualPrivateCloud("Google VPC")
            bastion = ComputeEngine("Bastion Host")
            gke = GKE("GKE")

            # VPC with Bastion Host
            vpc - Edge(style="dashed") >> [bastion, gke]

            bastion >> Edge(style="bold", color="darkgreen") >> gke

            # IaC for GKE
            tf >> Edge(label="GKE setup", color="purple", style="bold") >> [bastion, vpc, gke]
            jenkins << Edge(color="blue", style="bold") >> bastion

            with Cluster("GKE Cluster"):
                master = Master("Master Node")

                gke >> Edge(style="dashed", color="blue")  >> master

                with Cluster("Worker Node 1"):
                    node1 = Node("Worker Node (us-east1-b)")

                    with Cluster("Istio Service Mesh"):
                        # service mesh components
                        istio_ingress = Istio("Istio Ingress")
                        istio_service = Istio("Istio Service")

                        # API resources w/ Envoy Proxy - sidecar injection
                        with Cluster("Deployment"):
                            helm = Helm("Infra Helm Chart")
                            tf >> Edge(style="bold", color="purple") >> helm
                            hpa = HPA("Horizontal Pod AutoScaler")
                            api_deployment = Deploy("API deployment")
                            api_rs = RS("API ReplicaSet")
                            api_pods = []
                            with Cluster("API"):
                                for _ in range(3):
                                    pod = Pod("App")
                                    envoy_proxy = Envoy("Proxy")
                                    pod - envoy_proxy
                                    api_pods.append(api_rs >> pod)
                            helm >> hpa

                        with Cluster("Infra Dependencies"):
                            # DB resources
                            helm = Helm("Infra Helm Chart")
                            pg = Postgresql("Postgres DB")
                            pv = PV("Persistent Volume")
                            sc = SC("Storage Class")
                            db_pods = []
                            with Cluster("Stateful Database"):
                                db_stateful = STS("Postgres StatefulSet")
                                pg_hs = SVC("Postgres Headless SVC")
                                for _ in range(3):
                                    pod = Pod("App-DB")
                                    pvc = PVC("PVC")
                                    pod - db_stateful - pvc
                                    db_pods.append(pg_hs >> pod >> pvc)

                            db_pods << pv << sc

                            tf >> Edge(style="bold", color="purple") >> helm >> pg >> db_stateful
                            pg >> pg_hs

                            pg_hs << Edge(style="bold", color="orange") << istio_service << Edge(style="bold", color="orange") << api_pods

                        # Custom Kubernetes Operator for CronJob
                        with Cluster("Custom CronJob Kubernetes Operator"):
                            podOperator = Pod("k8s operator")
                            customCR = Pod("Custom Resource")
                            crd = CRD("Custom Resource Definition")
                            cronJob = Cronjob("CronJob")
                            job = Job("Job")
                            with Cluster("CronJob Configuration"):
                                cm = CM("ConfigMap")
                                secret = Secret("Secret")

                            source >> Edge(style="bold", color="purple") >> podOperator >> crd

                            crd << Edge(style="dashed") >> customCR
                            api_pods >> Edge(style="dotted", color="magenta") >> cm
                            api_pods >> Edge(style="dotted", color="magenta") >> secret
                            api_pods >> Edge(style="bold" , color="orange") >> istio_service >> Edge(style="bold", color="orange")>> customCR >> cronJob >> job

                            cm >> Edge(style="dashed") >> job
                            secret >> Edge(style="dashed") >> job


                        # Kafka Message Broker Architecture
                        with Cluster("Kafka Cluster"):
                            helm = Helm("Infra Helm Chart")
                            tf >> Edge(style="bold", color="purple") >> helm
                            producer = Pod("Producer")
                            consumer_db  = Postgresql("Consumer DB")
                            brokers = []
                            consumers = []
                            with Cluster("Kafka StatefulSet"):
                                zookeeper = Zookeeper("Zookeeper")
                                svc = SVC("Kafka Headless SVC")
                                for _ in range (3):
                                    consumer = Pod("Consumer")
                                    broker = Kafka("Kafka Broker")
                                    broker << Edge(style="dashed", color="darkred") << svc << Edge(style="dashed", color="darkred", label="Subscribe") << consumer
                                    brokers.append(broker)
                                    consumers.append(consumer)

                            list = [zookeeper, consumer_db , brokers]
                            for i in range(3):
                                helm >> Edge(style="dashed", color="lightpink") >> list[i]
                            zookeeper << Edge(style="dotted") >> brokers
                            job >> Edge(style="bold") >> producer
                            producer >> Edge(style="bold", color="darkgreen") >> brokers

                            consumers >> consumer_db

                with Cluster("Worker Node 2 \n (Similar to Worker Node 1)"):
                    node2 = Node("Worker Node (us-east1-c)")

                with Cluster("Worker Node 3 \n (Similar to Worker Node 1)"):
                    node3 = Node("Worker Node (us-east1-d)")

                master >> Edge(style="bold") >> [node1, node2, node3]
        istio_ingress >> hpa >> api_deployment >> api_rs >> api_pods
        users << Edge(style="bold", color="darkgreen") >> istio_ingress
        istio_ingress << Edge(style="bold", color="orange") >> api_pods

    # hosted website server
    with Cluster("                                                "):
        neu_server = Server("www.northeastern.edu")
        job >> Edge(style="dashed") >> neu_server
        job << Edge(style="dashed") << neu_server

