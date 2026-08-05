import os, docker

class DockerSandbox:
    def __init__(self, image: str = "python:3.11-slim"):
        self.client = docker.from_env()
        self.image = image

    def run_pytest(self, repo_path: str = ".") -> dict:
        abs_path = os.path.abspath(repo_path)
        # Force pip install pytest FIRST inside the container
        cmd = "sh -c 'pip install --no-cache-dir pytest >/dev/null 2>&1 && pytest'"
        try:
            container = self.client.containers.run(
                self.image, cmd, volumes={abs_path: {"bind": "/app", "mode": "rw"}},
                working_dir="/app", detach=True, network_mode="none", mem_limit="512m"
            )
            code = container.wait().get("StatusCode", -1)
            logs = container.logs().decode("utf-8")
            container.remove(force=True)
            
            failed_file = next((l.split("FAILED ")[1].split("::")[0].strip() 
                                for l in logs.splitlines() if l.startswith("FAILED ")), None)
            return {"passed": code == 0, "logs": logs, "failed_file": failed_file}
        except Exception as e:
            return {"passed": False, "logs": str(e), "failed_file": None}