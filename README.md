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
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/dev-smart-tool-batched.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/dev-smart-tool-batched.png)](https://supervise.ly)

</div>

# Overview

Application allows you to label objects with **Smart Tool using batch way**.

Application key points:
- Multiclass annotation
- Input data ordering
- Saves annotation progress automatically 
- Apply model to Objects (Rectangles) / whole Images
- Mark broken Objects / Images
- Linked green / red points between cards
- Flexible settings
- Doesn't change the Input Project

# Usage

📋 Content:

* <a href="#application-startup">Application Startup</a>
* <a href="#controls-with-shortcuts">Controls with Shortcuts</a>
* <a href="#general-usage-scenario">General Usage Scenario</a>  
* <a href="#cells-functionality">Cells Functionality</a>  
* <a href="#preferences-panel">Preferences Panel</a>  
* <a href="#control-panel">Control Panel</a>  


### Application Startup

1. On startup application will suggest **input data order.**<br> 
   For comfortable and efficient labeling we recommend to use sorted bboxes order.

<img src="https://imgur.com/IQhS6Bg.png" style="width: 100%;"/>

2. **Application saves annotation progress automatically.**<br>
If you launch application on same project a second time — 
   it will suggest you to continue the labeling process from the paused point.

<img src="https://imgur.com/n1oLkux.png" style="width: 100%;"/>


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

2. **Update Masks (<kbd>Shift</kbd> + <kbd>D</kbd>)** on all unupdated (orange) cells
<img src="https://imgur.com/IxcUVm3.png" style="width: 100%;"/>

3. **Unlink All (<kbd>Shift</kbd> + <kbd>Q</kbd>)** cells
<img src="https://imgur.com/5XkMWoI.png" style="width: 100%;"/>

4. Easily place **green points** to label-interested area and **red points** to label-not-interested area to correct local mistakes.
<img src="https://imgur.com/1ijrQpC.png" style="width: 100%;"/>

5. When you satisfied with results, click **Next Batch** button to load next images
<img src="https://imgur.com/HJaNRY3.png" style="width: 100%;"/>

### Cells Functionality

Batched Smart Tool consists of cells with objects to label.<br/>
Each cell has core functionality:

1. Linked Cell —  all points (green / red) on linked cells will synchronise.
2. Mark as Unlabeled — object will be marked with `_not_labeled_by_BTC` tag in output project.
3. Mark as Labeled — mark object as labeled (optional option).
4. Show in Input Project — open object in the Classic Labeling Interface.

<img src="https://imgur.com/CfpcuAY.png" style="width: 100%;"/>


### Preferences Panel

**Preferences Panel** allows you to customize labeling interface for your needs.
<img src="https://imgur.com/cYXObJB.png" style="width: 100%;"/>

**Grid Cells Preferences** allows you to adjust number, size, padding and masks opacity parameters for each cell in the grid.  
<img src="https://imgur.com/MrqTMmc.png" style="height: 60px;"/>

**Model Preferences** allows you to connect to served Smart Tool model, and select labeling mode.  
<img src="https://imgur.com/CSroTT2.png" style="height: 60px;"/>

**Apply model to Preference** allows you to choose input data for labeling.  
You can select objects (Rectangles) from prepared project or label whole images.  
   
<img src="https://imgur.com/y05aYwo.png" style="height: 60px;"/>  

`ℹ️ Multiclass labeling available`  
<img src="https://imgur.com/bJKavJA.png" style="width: 60%;"/>


### Control Panel

**Control Panel** allows you control labeling process.
<img src="https://imgur.com/DDTnoXW.png" style="width: 100%;"/>


**Link all (<kbd>Shift</kbd> + <kbd>E</kbd>)** — links all cells, all points (green / red) on linked cells will synchronise.  
**Unlink all (<kbd>Shift</kbd> + <kbd>Q</kbd>)** — unlinks all cells.  
<img src="https://imgur.com/iYBzz7m.png" style="height: 60px;"/>

**Assign Base (<kbd>Shift</kbd> + <kbd>A</kbd>)** — assign 8 red points to corners and 1 green point to center of image.    
**Clean Up (<kbd>Shift</kbd> + <kbd>C</kbd>)** — clean up data from all linked cells.   
<img src="https://imgur.com/y2SCqOu.png" style="height: 60px;"/>



**Update Masks (<kbd>Shift</kbd> + <kbd>D</kbd>)** — updates masks on all unupdated (orange) cells.  
**Next Batch** — uploads labeled data from cells to output project and load new data to label.  
<img src="https://imgur.com/Y9Mfxrc.png" style="height: 60px;"/>


# How to run


1. Prepare **Images Project**<br>
   
**Option 1:** with roughly assigned **Rectangles** 

<img src="https://github.com/supervisely-ecosystem/dev-smart-tool-batched/releases/download/v0.0.1/prepare-project.gif?raw=true" style="width: 100%;"/>

**Option 2:** with plain images
<img src="https://imgur.com/qSY467f.png" style="width: 100%;"/>





2. Launch [RITM interactive segmentation Smart Tool](https://ecosystem.supervise.ly/apps/supervisely-ecosystem%252Fritm-interactive-segmentation%252Fsupervisely)

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/ritm-interactive-segmentation/supervisely" src="https://i.imgur.com/eWmFwQ9.png" width="600px" style='padding-bottom: 0'/>  



3. Add [Batched Smart Tool](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/dev-smart-tool-batched) to your Team

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/dev-smart-tool-batched" src="https://imgur.com/KkM6dO0.png" width="350px">


4. Launch from context menu of prepared project

<img src="https://imgur.com/YrAQeRi.png" style="width: 100%;"/>




