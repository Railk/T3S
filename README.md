TSS Sublime (T3S)
----------------------------------------------------------------------------

### STATUS : Not maintained

Due to a lack of time, the lack of will to continue working on it and the fact that i've changed my code editor, this plugin will no longer be maintained. I've created this plugin mainly so i could code with typescript on sublime text, it served me well and i hope it helped others too, luckily there's other options right now for people using sublimetext :

. ArcticTypescript a fork of TS3 with lots of change and work to tackle performance issues : 
	https://github.com/Phaiax/ArcticTypescript

. And microsoft official sublimetext typescript plugin : 
	https://github.com/Microsoft/TypeScript-Sublime-Plugin

Thx to all the people who contributed to this plugin

See you space cowboys

### INFO
TypeScript plugin for Sublime Text 2 and 3 using TypeScript tools : https://github.com/clausreinke/typescript-tools

I'm using the same error icons has SublimeLinter.
I took inspiration from: https://github.com/raph-amiard/sublime-typescript

### Next version
A new version of the plugin is currently in developement in the <code>Dev Branch</code>. This new version correct most of the problem of the current version (especially references tracking after project initialisation that in the current version is not working) and have new features. It will be released soon.


### v0.2.0 Changes (updates i make can break some things as i don't always fully check on each OS)
- On focusing a ts file if no project is found for it; a project creation process begin
- You need to redo your project settings as i've added the possibility to have settings per project (cf. examples)
- You need to redo your user settings as the file name have changed to reflect the plugin name
- Error and Outline panels have been replaced by views (you can click on each line to go to the corresponding place)
- Build system is integrated to the plugin (you still need <code>tsc</code>) and you can set your node path (settings)
- You can build on save (settings) and have a the current file resulting javascript file in a split view (settings)
- When you close all the ts file of a project, the project (and the node corresponding node process) is closed
- One branch only for Sublime text 2 and 3
- Completion on <code>:</code> with <code>ctrl+space</code> to have the primitives and interface
- Quick panel for user message (initialisation,closing project etc...)
- Todo : 

	1. Better layout management
	2. Tests everything on OSes and ST2/ST3


### Features
- TypeScript language auto completion
- TypeScript language error highlighting
- TypeScript language syntax highlighting
- A build System
- Basic refactoring


### Dependencies
- node.js
- tsc for the build system that you install via <code>npm install -g typescript</code> (http://www.typescriptlang.org/)


### OS
Tested on Windows & Ubuntu & OSX not entirely for now on <code>DEV</code>

<<<<<<< HEAD
=======
### Known Problems
- OSX has currently the path for node hardcoded (default installation directory) due to some environnment <code>PATH</code> for GUI app problem. (OSX path settings added on v0.2.0 <code>dev</code> branch version soon to be released)
- Adding reference after loading a project doesn't track them correctly (resolved on v0.2.0 <code>dev</code> branch version soon to be released)
>>>>>>> master

### Installation

##### Sublime text Package directory:
Click the <code>Preferences > Browse Packages…</code> menu


##### Without Git:
Download the latest source zip from github and extract the files to your Sublime Text <code>Packages</code> directory, into a new directory named <code>T3S</code>.

##### With Git:
1. Clone the repository in your Sublime Text <code>Packages</code> directory.
2. Checkout dev branch using <code>git checkout dev</code>.


### Project

For the plugin to work you need to define a project :


1. Inside your <code>project_name.sublime-project</code> file if you have one
2. By creating a <code>.sublimets</code> at the root of your project folder

<<<<<<< HEAD
You can look inside the <code>example folder</code> for setup examples or if you focus a ts file and no project are found a project creation porcess will be initiated
=======
##### With Git:
1. Clone the repository in your Sublime Text <code>Packages</code> directory.
2. Checkout ST2 branch using <code>git checkout ST2</code>.


### Project Settings:

To use the plugin correctly you need to setup a project either via a .sublimets file or using the sublime-project file.

When using .sublimets or a .sublime-project file, you need to open the folder where your project is with <code>file > open folder</code> or <code>project > open project</code> in Sublime Text.

##### sublime-project file
You can setup multiple root files
You can indicate your typescript root files in your project_name.sublime-project like so :
>>>>>>> master

To open a project, you need to open the folder where your project is with <code>file > open folder</code> or <code>project > open project</code>
	
##### You have a sublime text project or want to create a project with multiple root files
You can indicate your typescript root files in your project_name.sublime-project like so :

	"settings":
	{
			"typescript":
			{
				"roots":[
					"path/from/top/folder/to/your/root/file_1.ts",
					"path/from/top/folder/to/your/root/file_2.ts",
					...
					"path/from/top/folder/to/your/root/file_X.ts"
				]
			}
	}

And also add (optionnal) your project settings :

		"settings":
		{
			"typescript":
			{
				"roots":[
					"path/from/top/folder/to/your/root/file_1.ts",
					"path/from/top/folder/to/your/root/file_2.ts",
					...
					"path/from/top/folder/to/your/root/file_X.ts"
				],
				"settings":{
					"auto_complete":true,
					"node_path":"none",
					"error_on_save_only":false,
					"build_on_save":false,
					"show_build_file":false,
					"build_parameters":{
						"pre_processing_commands":[],
						"post_processing_commands":[],
						"output_dir_path":"none",
						"concatenate_and_emit_output_file_path":"none",
						"source_files_root_path":"none",
						"map_files_root_path":"none",
						"module_kind":"none",
						"allow_bool_synonym":false,
						"allow_import_module_synonym":false,
						"generate_declaration":false,
						"no_implicit_any_warning":false,
						"skip_resolution_and_preprocessing":false,
						"remove_comments_from_output":false,
						"generate_source_map":false,
						"ecmascript_target":"ES3"
					}
				}
			}
		}


##### You want to create a single root file project and don't want to create a sublime-project
You can create a .sublimets file in the folder containing the typescript root file :

	{
			"root":"root_file_name.ts"
	}

And also add (optionnal) your project settings :

		{
			"root":"root_file_name.ts",
			"settings":{
				"auto_complete":true,
				"node_path":"none",
				"error_on_save_only":false,
				"build_on_save":false,
				"show_build_file":false,
				"build_parameters":{
					"pre_processing_commands":[],
					"post_processing_commands":[],
					"output_dir_path":"none",
					"concatenate_and_emit_output_file_path":"none",
					"source_files_root_path":"none",
					"map_files_root_path":"none",
					"module_kind":"none",
					"allow_bool_synonym":false,
					"allow_import_module_synonym":false,
					"generate_declaration":false,
					"no_implicit_any_warning":false,
					"skip_resolution_and_preprocessing":false,
					"remove_comments_from_output":false,
					"generate_source_map":false,
					"ecmascript_target":"ES3"
				}
			}
		}

### Commands:

1. <code>f1</code> Click on a property, a class, a method etc... then press f1 to have detail about it (ST3 ONLY)
2. <code>f2</code> Click on a property, a class, a method etc... then press f2 to refactor the member (EXPERIMENTAL use at your own risk)
2. <code>f3</code> Open a outline <code>view</code> of the file (class,methods,properties, etc...)
3. <code>f4</code> Click on a property, a class, a method etc... then press f4 to go to the definition
4. <code>f5</code> Reload the current project
5. <code>f8</code> or <code>ctrl+b</code> Build the project
6. <code>ctrl+shift+e</code> Open a <code>view</code> listing all the errors across all the files of the project

<<<<<<< HEAD
### Settings:
You can acces the plugin settings from <code>Preferences > Packages Settings > T3S</code>, to modify the settings please copy the default settings inside the user settings one, and make your modification there otherwise your settings will be override by an update of the plugin, or put the settings inside your project file.

=======
		"settings":
		{
			"typescript":
			[
				"path/from/project/folder/to/your/root/file_1.ts",
				"path/from/project/folder/to/your/root/file_2.ts",
				...
			]
		}



##### .sublimets file:
You can setup only one root file.
You can create a .sublimets file in the folder containing the typescript root file


		{
			"root":"root_file_name.ts"
		}


If you don't chose either of these solutions the plugin wil launch a process for each file, making them not being able to talk to each other.


### Plugin settings:
You can acces the plugin settings from <code>Preferences > Packages Settings > T3S</code>, to modify the settings please copy the default settings inside the user settings one, and make your modification there otherwise your settings will be override by an update of the plugin.
>>>>>>> master

You have 6 settings available:

1. <code>auto_complete</code>: if you want to have sublime normal completion with typescript completion
2. <code>node_path</code>: to set you node path
3. <code>error_on_save_only</code>: to highlight errors only while saving or while typing, the default is showing error highlighting while typing
4. <code>build_on_save</code>: to build the project each time you save
5. <code>show_build_file</code>: to show the resulting javascript file of the current TypeScript file in a split view when building
6. the build parameters


		{
			"auto_complete":true,
			"node_path":"none",
			"error_on_save_only":false,
			"build_on_save":false,
			"show_build_file":false,
			"build_parameters":{
				"pre_processing_commands":[],
				"post_processing_commands":[],
				"output_dir_path":"none",
				"concatenate_and_emit_output_file_path":"none",
				"source_files_root_path":"none",
				"map_files_root_path":"none",
				"module_kind":"none",
				"allow_bool_synonym":false,
				"allow_import_module_synonym":false,
				"generate_declaration":false,
				"no_implicit_any_warning":false,
				"skip_resolution_and_preprocessing":false,
				"remove_comments_from_output":false,
				"generate_source_map":false,
				"ecmascript_target":"ES3"
			}
		}

##### auto_complete:
you can have normal sublime auto completion with typescript completion (if changed you need to restart sublime)

		"auto_complete":true|false

<<<<<<< HEAD
=======

		"local_tss":true


>>>>>>> master

##### node_path:
You can set the path to node : (if changed you need to restart sublime)

<<<<<<< HEAD
		"node_path":"/your/path/to"
		
		
=======

		"local_tss":false



>>>>>>> master
##### error_on_save_only:
Error highlighting while typing (will lag a bit du to calculation and this cannot be changed):


		"error_on_save_only":false


Error highlighting only shown when saving:


		"error_on_save_only":true


##### build_on_save:
On save the file can be automaticaly built or not :

		"build_on_save":true|false


##### show_build_file:
You can show the resulting javascript file of the current TypeScript file in a split view when building :

		"show_build_file":true|false


##### build_parameters:
I've added a build system that take most of the command line parameters of TSC, i'll not explain them here, you can install TSC and look at the parameters via <code>tsc -h</code>

And you also have two extra parameters that are <code>pre_processing_commands</code> and <code>post_processing_commands</code> that give you the opportunity to do command line things before and after <code>tsc</code> compiling

These are the default values:


		"build_parameters":{
			"pre_processing_commands":[],
			"post_processing_commands":[],
			"output_dir_path":"none",
			"concatenate_and_emit_output_file_path":"none",
			"source_files_root_path":"none",
			"map_files_root_path":"none",
			"module_kind":"none",
			"allow_bool_synonym":false,
			"allow_import_module_synonym":false,
			"generate_declaration":false,
			"no_implicit_any_warning":false,
			"skip_resolution_and_preprocessing":false,
			"remove_comments_from_output":false,
			"generate_source_map":false,
			"ecmascript_target":"ES3"
		}

Here's an exemple that do:

1. One pre processing command : <code>node .settings/.components</code>
2. The actual compilation with an output dir and amd module : <code>tsc /absolute/path/to/filename.ts --outDir ./.build --module amd</code>
3. Two post processing commands : <code>node .settings/.silns.js</code> and <code>r.js.cmd -o .settings/.build.js</code>

		"build_parameters":{
			"pre_processing_commands":[
				"node .settings/.components"
			],
			"post_processing_commands":[
				"node .settings/.silns.js",
				"r.js.cmd -o .settings/.build.js"
			],
			"output_dir_path":"./.build",
			"concatenate_and_emit_output_file_path":"none",
			"source_files_root_path":"none",
			"map_files_root_path":"none",
			"module_kind":"amd",
			"allow_bool_synonym":false,
			"allow_import_module_synonym":false,
			"generate_declaration":false,
			"no_implicit_any_warning":false,
			"skip_resolution_and_preprocessing":false,
			"remove_comments_from_output":false,
			"generate_source_map":false,
			"ecmascript_target":"ES3"
		}

### Commands:

<<<<<<< HEAD
### Usage:
=======
1. <code>f1</code> Click on a property, a class, a method etc... then press f1 to have detail about it (doc comments etc...) (sublime text 3 only)
2. <code>f3</code> Open a panel to Navigate in file (class,methods,properties, etc...)
3. <code>f4</code> Click on a property, a class, a method etc... then press f4 to go to the definition
4. <code>f5</code> Reload the current project
5. <code>ctrl+shift+e</code> Open a panel listing all the errors across all the files of the project
6. <code>ctrl+shift+K</code> Close all projects (to reinialise just focus on/open a .ts file)



>>>>>>> master

##### Initialisation:
When you load a .ts file the plugin will initialize the root file or the current file and it can take some time for huge project.

The Sublime Text Status bar will indicate Typescript initializing during this phase and disapear when it's finished

<<<<<<< HEAD
##### Show Type:
=======
##### References file
if you change a references file or make a change in a definition file and completion don't show up as it should, please use <code>F5</code> to reload the project

##### Show Type: (sublime text 3 only)
>>>>>>> master
you can click on variable or a method and press <code>F1</code> to have detail about it (doc comments etc...)

##### Got to definition:
you can click on variable or a method and press <code>F4</code> to go to the definition

<<<<<<< HEAD
##### Outline View:
you can open an <code>Outline view</code> by pressing <code>F3</code> on a file to list class variables and methods tou can then click on an item to scroll towards it
=======
##### Navigate in file:
you can open a panel by pressing <code>F3</code> on a file to list class variables and methods tou can then click on an item to scroll towards it
>>>>>>> master

##### Auto-completion:
You can circle through the function variables (if there's some) like with the snippets with the <code>tab</code> key

##### Error highlighting:
You can click on highlighted part to see the error description in the status bar

<<<<<<< HEAD
##### Error View: 
You have the possibility to open an <code>Error view</code> that will list all the errors accross all your project file with the command <code>ctrl+shift+e</code>
=======
##### Error Panel:
You have the possibility to open an <code>error panel</code> that will list all the errors accross all your project file with the command <code>ctrl+shift+e</code>
>>>>>>> master
You can then click on each row, it'll open or focus the already open file concerned by the error.

##### Reloading the project:
You have the possibility to <code>reload</code> the project by pressing <code>F5</code>, you can see in the console when the reload is finished

<<<<<<< HEAD
##### Building the project:
you can build the current project with <code>F8</code> on a file. if you have activated <code>show_build_file</code> option it will show a <code>Split view</code> with the corresponding javascript file

=======
##### Closing all project:
You have the possibility to <code>close</code> all projects by pressing <code>ctrl+shift+k</code>, you can then reinitialise a project by focusing one of the file of the project
>>>>>>> master
