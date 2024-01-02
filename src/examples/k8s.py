from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.ci import GithubActions, Jenkins
from diagrams.onprem.client import Client,Users
from diagrams.custom import Custom
from diagrams.aws.compute import Compute
from diagrams.gcp.compute import ComputeEngine, GKE
from diagrams.k8s.infra import Master, Node
from diagrams.k8s.compute import Pod, Deployment, RS, StatefulSet
from diagrams.k8s.network import Service
from diagrams.k8s.others import CRD
from diagrams.k8s.compute import Cronjob, Job
from diagrams.k8s.podconfig import ConfigMap, Secret
from diagrams.onprem.queue import  Kafka
from diagrams.onprem.network import Zookeeper
from diagrams.onprem.compute import Server

with Diagram("CSYE7125", show=True):
    with Cluster("User Cluster"):
        users = Users("users")

    with Cluster("Github Cluster"):
        ghActions = GithubActions("CI")
        client = Client("user")
        webHookCustom = Custom("webhook" , "./my_resources/webhook.png")
        # edges for client commit and ci runs

    with Cluster("AWS-Jenkins Cluster"):
        jenkinsEc2 = Compute("Jenkins Server")
        jenkins = Jenkins("Jenkins")

        client >> Edge(label="commit") >> ghActions >> Edge(label="triggers") >> webHookCustom >> jenkinsEc2 << Edge(color="red", style="dotted") << jenkins

    with Cluster("GCP Cloud"):
        with Cluster("Bastion Cluster"):
            bastion = ComputeEngine("Bation Host")

            jenkinsEc2 >> bastion

            with Cluster("GKE Cluster"):
                gke = GKE("GKE")
                master = Master("master")


                bastion >> Edge(style="dotted", color="blue")  >> master

                with Cluster("Node group 1"):
                    node1 = Node("node 1")


                    with Cluster("Node1 Setup"):
                        webapp_deployment = Deployment("webapp deployment")
                        webapp_rs = RS("webapp rs")
                        webapp_service = Service("webapp service")
                        pod1 = Pod("webapp 1")
                        pod2 = Pod("webapp 2")
                        pod3 = Pod("webapp 3")

                        # DB
                        webapp_stateful = StatefulSet("webapp statefulset")
                        webappdb1 = Pod("webapp-db 1")
                        webappdb2 = Pod("webapp-db 2")
                        webappdb3 = Pod("webapp-db 3")

                        master >> Edge(style="bold") >> webapp_deployment >> webapp_rs
                        master >> Edge(style="bold") >> webapp_stateful

                        # service to webapp pods
                        webapp_service >> Edge(style="dashed" , color='darkgreen') >> [pod1 , pod2, pod3]

                        webapp_rs >> [pod1 , pod2, pod3]

                        webapp_stateful >> Edge(style="bold") >> [webappdb1,webappdb2,webappdb3]

                        pod1 >> Edge(style="bold" , color="red") >> webappdb1
                        pod2 >> Edge(style="bold", color="blue") >> webappdb2
                        pod3 >> Edge(style="bold", color="orange") >> webappdb3

                with Cluster("Node group 2"):
                    node1 = Node("node 2")

                    with Cluster("Node2 Setup"):
                        podOperator = Pod("k8s operator")
                        customCR = Custom("custom resource", "./my_resources/pod.png")
                        crd = CRD("CRD")
                        cronJob = Cronjob("cj")
                        job = Job("job")
                        cm = ConfigMap("cm")
                        secret = Secret("secret")

                        pod1 >> Edge(style="bold" , color="orange") >> customCR >> cronJob
                        cronJob >> job
                        cm >> Edge(style="dashed") >> job
                        secret >> Edge(style="dashed") >> job
                        podOperator >> crd


                with Cluster("Kafka Cluster"):
                    broker1 = Kafka("broker 1")
                    zookeeper = Zookeeper("zk1")
                    consumer_pod1 = Pod("consumer pod 1")
                    consumer_db  = Pod("consumer db")
                    zookeeper >> broker1
                    consumer_service = Service("consumer service")
                    job >> Edge(style="bold") >> broker1

                    consumer_pod1 >> Edge(style="dashed", color="darkred", label="polling") >> broker1
                    consumer_pod1 >> consumer_service >> consumer_db



        users >> Edge(style="dashed" , label="POST req") >> webapp_service

    with Cluster("Neu Server Cluster"):
        neu_server = Server("www.northeastern.edu")
        job >> Edge(style="dashed", label="request") >> neu_server
        job << Edge(style="dashed", label="response") << neu_server

