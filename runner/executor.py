import subprocess

def executar_script(nome_script):

    processo = subprocess.Popen(
        ["python", nome_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    logs = []

    for linha in processo.stdout:
        logs.append(linha)

    processo.wait()

    return logs