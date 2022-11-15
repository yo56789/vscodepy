## Example

#### Code

[//]: # (```py)

[//]: # (import vscode)

[//]: # (from vscode.config import Config)

[//]: # ()
[//]: # (c = Config&#40;name='Say', description='Say Something!', input_type=str, default="Hello World!"&#41;)

[//]: # (ext = vscode.Extension&#40;'speaker','Speaker', '0.0.1', config=[c]&#41;)

[//]: # ()
[//]: # (@ext.command&#40;&#41;)

[//]: # (def message_say_config&#40;&#41;:)

[//]: # (    vscode.window.show_info_message&#40;ext.get_config&#40;'Say'&#41; or c.default&#41;)

[//]: # ()
[//]: # (vscode.build&#40;ext&#41;)

[//]: # (```)

#### Result

<img src="https://i.imgur.com/LkCwdCT.gif"/>

# Workspace Configurations

[//]: # (::: vscode.config)
