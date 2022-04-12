<div align="center" markdown>
<img src="https://github.com/supervisely-ecosystem/dev-smart-tool-batched/releases/download/v0.0.1/batch_smart_tool_demo.gif?raw=true" style="width: 100%;"/>

# Batched Smart Tool

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Usage">Usage</a> •
  <a href="#how-to-run">How to run</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/dev-smart-tool-batched)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/dev-smart-tool-batched)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/dev-smart-tool-batched&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/dev-smart-tool-batched&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/dev-smart-tool-batched&counter=runs&label=runs&123)](https://supervise.ly)

</div>

# Overview

Application allows you to label objects with **Smart Tool using batch way**.

Application key points:  
- Multiclass annotation
- Input data ordering
- Apply model to Objects (Rectangles) / whole Images
- Mark broken Objects / Images
- Linked green / red points between cards
- Flexible settings
- Saves the progress of an annotation

# Usage

📋 Content:

* <a href="#controls-with-shortcuts">Controls with Shortcuts</a>  
* <a href="#general-usage-scenario">General Usage Scenario</a>  
* <a href="#settings-board">Settings Board</a>  


### Controls with Shortcuts
| Key                                                           | Description                               |
| ------------------------------------------------------------- | ------------------------------------------|
| <kbd>Left Mouse Button</kbd>                                  | Place a green point |
| <kbd>Left Mouse Button</kbd> + <kbd>Shift</kbd>          | Place a red point               |
| <kbd>Left Mouse Button</kbd> + <kbd>Ctrl</kbd>           | Remove point                              |
| <kbd>Scroll Wheel</kbd>                                       | Zoom an image in and out                  |
| <kbd>Right Mouse Button</kbd> + <kbd>Move Mouse</kbd>    | Move an image                             |
| <kbd>Shift</kbd> + <kbd>E</kbd>    |      Link All Cells                        |
| <kbd>Shift</kbd> + <kbd>Q</kbd>    |      Unlink All Cells                        |
| <kbd>Shift</kbd> + <kbd>A</kbd>    |      Assign Points Automatically                        |
| <kbd>Shift</kbd> + <kbd>D</kbd>    |      Update Unupdated Cells                         |
| <kbd>Shift</kbd> + <kbd>C</kbd>    |      Clean All Linked Cells                        |

### General Usage Scenario

1. **Assign Base (<kbd>Shift</kbd> + <kbd>A</kbd>)** points to all linked cells
<img src="https://imgur.com/nE0CP4N.png" style="width: 100%;"/>  

2. **Update Masks (<kbd>Shift</kbd> + <kbd>D</kbd>)** on all unupdated cells
<img src="https://imgur.com/IxcUVm3.png" style="width: 100%;"/>

3. **Unlink All (<kbd>Shift</kbd> + <kbd>Q</kbd>)** cells
<img src="https://imgur.com/5XkMWoI.png" style="width: 100%;"/>

4. Easily place **green points** to label-interested area and **red points** to label-not-interested area to correct local mistakes.
<img src="https://imgur.com/1ijrQpC.png" style="width: 100%;"/>

5. When you satisfied with results, click **Next Batch** button to load next images
<img src="https://imgur.com/HJaNRY3.png" style="width: 100%;"/>

### Preferences Panel

**Preferences Panel** allows you to customize labeling interface for your needs.  

<img src="https://imgur.com/cYXObJB.png" style="width: 100%;"/>

**Cells Settings**

<img src="https://imgur.com/MrqTMmc.png" style="width: 40%;"/>



# How to run


1. Prepare **Images Project** with roughly assigned **Rectangles**

<img src="https://github.com/supervisely-ecosystem/dev-smart-tool-batched/releases/download/v0.0.1/prepare-project.gif?raw=true" style="width: 100%;"/>

2. Launch [RITM interactive segmentation Smart Tool](https://ecosystem.supervise.ly/apps/supervisely-ecosystem%252Fritm-interactive-segmentation%252Fsupervisely)

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/ritm-interactive-segmentation/supervisely" src="https://i.imgur.com/eWmFwQ9.png" width="600px" style='padding-bottom: 0'/>  



3. Add [Batched Smart Tool](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/dev-smart-tool-batched) to your Team

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/dev-smart-tool-batched" src="https://imgur.com/KkM6dO0.png" width="350px">


4. Launch from context menu of prepared project

<img src="https://imgur.com/YrAQeRi.png" style="width: 100%;"/>




