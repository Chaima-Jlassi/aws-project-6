"""Generates docs/architecture.png

Usage:
    pip install diagrams      # also needs Graphviz installed
    python3 docs/architecture.py
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECR, Fargate
from diagrams.aws.database import ElasticacheForRedis
from diagrams.aws.devtools import Codedeploy, Codepipeline, XRay
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import ALB, CloudMap, InternetGateway, NATGateway
from diagrams.aws.security import SecretsManager
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.client import Users
from diagrams.onprem.vcs import Github

graph_attr = {
    "fontsize": "22",
    "labelloc": "t",
    "pad": "0.5",
    "nodesep": "0.6",
    "ranksep": "1.3",
    "splines": "spline",
}

with Diagram(
    "Containerized Microservices on ECS Fargate",
    filename="docs/architecture",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
):
    users = Users("Internet users")

    with Cluster("CI/CD"):
        repo = Github("GitHub repo")
        gha = GithubActions("GitHub Actions\nbuild, test, scan")
        pipeline = Codepipeline("CodePipeline")
        deploy = Codedeploy("CodeDeploy\nblue/green + rollback")
        repo >> gha
        repo >> pipeline >> deploy

    with Cluster("AWS Region"):
        ecr = ECR("ECR\nscan on push")
        secrets = SecretsManager("Secrets Manager\nJWT secret")

        with Cluster("VPC 10.0.0.0/16"):
            igw = InternetGateway("Internet Gateway")

            with Cluster("Public subnets (AZ-a, AZ-b)"):
                alb = ALB("Application\nLoad Balancer")
                nat = NATGateway("NAT Gateway")

            with Cluster("Private subnets (AZ-a, AZ-b)"):
                cloudmap = CloudMap("Cloud Map\nprivate DNS (*.local)")

                with Cluster("ECS Cluster (Fargate)"):
                    auth = Fargate("auth")
                    orders = Fargate("orders")
                    notif = Fargate("notifications")

                redis = ElasticacheForRedis("ElastiCache Redis\nshared sessions")

        cw = Cloudwatch("CloudWatch\nlogs, alarms")
        xray = XRay("X-Ray\nservice map")

    # Ingress
    users >> igw >> alb
    alb >> Edge(label="/auth/*") >> auth
    alb >> Edge(label="/orders*") >> orders
    alb >> Edge(label="/notify*") >> notif

    # Service-to-service through Cloud Map DNS
    orders >> Edge(label="verify token\nauth.local", style="dashed") >> auth
    orders >> Edge(label="notify\nnotifications.local", style="dashed") >> notif

    # Data and secrets
    auth >> Edge(label="sessions") >> redis
    secrets >> Edge(label="injected at\ntask start", style="dotted") >> auth

    # Image path
    gha >> Edge(label="push image") >> ecr
    nat >> Edge(label="pull image", style="dotted") >> ecr
    deploy >> Edge(label="blue/green\nshift traffic") >> alb

    # Observability
    notif >> Edge(style="dotted", color="darkgreen") >> cw
    orders >> Edge(style="dotted", color="darkgreen") >> xray
