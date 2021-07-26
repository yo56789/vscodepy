import os
import json
import time
import inspect


def create_package(data, config):
    package_name = data["name"]
    package = {
        "name": package_name,
        "displayName": data.get("display_name", package_name),
        "description": data.get("description", ""),
        "version": data["version"],
        "engines": {"vscode": "^1.58.0"},
        "categories": ["Other"],
        "main": "./build/extension.js",
    }
    package.update(config)
    return package


extensions_json = {"recommendations": ["dbaeumer.vscode-eslint"]}

launch_json = {
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Extension",
            "type": "extensionHost",
            "request": "launch",
            "args": ["--extensionDevelopmentPath=${workspaceFolder}"],
        },
        {
            "name": "Extension Tests",
            "type": "extensionHost",
            "request": "launch",
            "args": [
                "--extensionDevelopmentPath=${workspaceFolder}",
                "--extensionTestsPath=${workspaceFolder}/test/suite/index",
            ],
        },
    ],
}

main_py = """\n
import sys
def ipc_main():
    globals()[sys.argv[1]]()

ipc_main()
"""


def build_py(functions):
    pre = "# Built using vscode-ext\n\n"
    with open(inspect.getfile(functions[0]), "r") as f:
        imports = pre + "".join([l for l in f.readlines() if not ".build(" in l])
    imports += "\n"
    main = main_py
    code = imports + main
    return code


def build_js(name, events, commands):
    cwd = os.getcwd()
    python_path = os.path.join(cwd, "build", "extension.py").replace("\\", "\\\\")

    imports = ""
    directory, filename = os.path.split(inspect.getfile(build_py))
    with open(os.path.join(directory, "main.js"), "r") as f:
        imports += f.read()
    on_activate = events.get("activate")
    code_on_activate = "function activate(context) {\n"
    if on_activate:
        code_on_activate += f'console.log("{on_activate()}");\n'

    for command in commands:
        code_on_activate += (
            f"let {command.name} = vscode.commands.registerCommand('{command.extension(name)}',"
            + "async function () {\n"
        )
        code_on_activate += (
            f'let py = spawn("python", [pythonPath,"{command.func_name}"]);\n'
        )
        code_on_activate += """
py.stdout.on("data", (data) => {
    executeCommands(py, data);
});
"""
        code_on_activate += "});\n"
        code_on_activate += f"context.subscriptions.push({command.name});\n"

    code_on_activate += "}\n"

    on_deactivate = events.get("deactivate")
    code_on_deactivate = "function deactivate() {"
    if on_deactivate:
        code_on_activate += f'\nconsole.log("{on_deactivate()}");\n'
    code_on_deactivate += "}"
    main = code_on_activate + "\n" + code_on_deactivate
    exports = "module.exports = {activate,deactivate}"
    code = f"{imports}\n{main}\n\n{exports}"
    return code


def create_files(package, javascript, python, publish, config):
    cwd = os.getcwd()

    # ---- Static ----

    vscode_path = os.path.join(cwd, ".vscode")
    os.makedirs(vscode_path, exist_ok=True)
    os.chdir(vscode_path)

    with open("extensions.json", "w") as f:
        json.dump(extensions_json, f, indent=2)

    with open("launch.json", "w") as f:
        json.dump(launch_json, f, indent=2)

    # ---- Dynamic ----
    package.update(config)
    with open(os.path.join(cwd, "package.json"), "w") as f:
        json.dump(package, f, indent=2)

    build_path = os.path.join(cwd, "build")
    os.makedirs(build_path, exist_ok=True)
    os.chdir(build_path)
    with open("extension.js", "w") as f:
        f.write(javascript)

    with open("extension.py", "w") as f:
        f.write(python)
    os.chdir(cwd)

    if publish:
        with open("README.md", "w") as f:
            pass
        with open("CHANGELOG.md", "w") as f:
            pass
        if not os.path.isfile(".vscodeignore"):
            with open(".vscodeignore", "w") as f:
                f.write(".vscode/**")


def build(extension, publish=False, config=None):
    if config is None:
        config = {}
    if publish:
        if config.get("publisher") is None:
            config["publisher"] = input("Enter publisher name: ")

    print(f"\033[1;37;49mBuilding Extension {extension.name}...", "\033[0m")
    start = time.time()

    ext_data = extension.__dict__
    package_name = ext_data["name"]

    commands = []
    activation_events = []
    for command in ext_data.get("commands"):
        cmd = {"command": f"{package_name}.{command.name}", "title": command.title}
        if command.category is not None:
            cmd.update({"category": command.category})
        event = "onCommand:" + command.extension(package_name)
        commands.append(cmd)
        activation_events.append(event)
    package_config = {
        "contributes": {
            "commands": commands,
        },
        "activationEvents": activation_events,
    }
    if extension.keybindings:
        package_config["contributes"].update({"keybindings": extension.keybindings})

    if extension.activity_bar:
        package_config["contributes"]["viewsContainers"] = {
            "activitybar": [extension.activity_bar]
        }
        view = {
            extension.activity_bar["id"]: [
                {
                    "id": extension.activity_bar["id"],
                    "name": extension.activity_bar["title"],
                }
            ]
        }
        if package_config["contributes"].has_key("views"):
            package_config["contributes"]["views"].update(view)
        else:
            package_config["contributes"]["views"] = view

    package = create_package(ext_data, package_config)
    javascript = build_js(package_name, ext_data["events"], ext_data["commands"])
    python = build_py([c.func for c in ext_data["commands"]])
    create_files(package, javascript, python, publish, config)
    end = time.time()
    time_taken = round((end - start) * 1000, 2)
    print(f"\033[1;37;49mBuild completed successfully in {time_taken} ms!", "\033[0m")
