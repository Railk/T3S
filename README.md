TSS Sublime (T3S)
----------------------------------------------------------------------------

TypeScript plugin for Sublime Text 2 and 3 using TypeScript tools : https://github.com/clausreinke/typescript-tools

I'm using the same error icons has SublimeLinter.
I took inspiration from: https://github.com/raph-amiard/sublime-typescript


### v0.2.0 Changes (it's in beta for now, so bugs are still present and my updates can break things)
- You need to redo you user settings as the file name have changed to reflect the plugin name
- Error and Outline panels have been replaced by views (you can click on each line to go to the corresponding place)
- Build system is integrated to the plugin (you still need <code>tsc</code>) and you can set your node path (settings)
- You can have a split view showing the current active ts file corresponding javascript file (settings)
- When you close all the ts file of a project, the project (and the node corresponding node process) is closed
- One branch only for Sublime text 2 and 3
- You can build on save (settings)
- Completion on <code>:</code> with <code>ctrl+space</code> to have the primitives and interface
- Quick panel for user message (initialisation,closing project etc...)
- Todo : 

	- Better layout management
	- Per Project settings


### Features
- TypeScript language auto completion
- TypeScript language error highlighting
- TypeScript language syntax highlighting
- A build System


### Dependencies
- node.js
- tsc for the build system that you install via <code>npm install -g typescript</code> (http://www.typescriptlang.org/)


### OS
Tested on Windows & Ubuntu & OSX


### Installation

##### Sublime text Package directory:
Click the <code>Preferences > Browse Packages…</code> menu


##### Without Git: 
Download the latest source zip from github and extract the files to your Sublime Text <code>Packages</code> directory, into a new directory named <code>T3S</code>.

##### With Git:
1. Clone the repository in your Sublime Text <code>Packages</code> directory.
2. Checkout dev branch using <code>git checkout dev</code>.


### Settings:
You can acces the plugin settings from <code>Preferences > Packages Settings > T3S</code>, to modify the settings please copy the default settings inside the user settings one, and make your modification there otherwise your settings will be override by an update of the plugin.

You have 5 settings available:

1. <code>node_path</code>: to set you node path
2. <code>error_on_save_only</code>: to highlight errors only while saving or while typing, the default is showing error highlighting while typing
3. <code>build_on_save</code>: to build the porject each time you save
4. <code>show_build_file</code>: to show the resulting javascript file of the current TypeScript file in a split view when building
5. the build parameters


		{
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


##### node_path:
You can set the path to node : (if changed you need to restart sublime)

		"node_path":"/your/path/to"
		
		
##### error_on_save_only:
Error highlighting while typing (will lag a bit du to calculation and this cannot be changed):

		
		"error_on_save_only":false
		

Error highlighting only shown when saving:

		
		"error_on_save_only":true


##### build_on_save:
On save the file can be automaticaly or not :

		"build_on_save_only":true|false


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

1. <code>f1</code> Click on a property, a class, a method etc... then press f1 to have detail about it (ST3 ONLY)
2. <code>f3</code> Open a outline <code>view</code> of the file (class,methods,properties, etc...)
3. <code>f4</code> Click on a property, a class, a method etc... then press f4 to go to the definition
4. <code>f5</code> Reload the current project
5. <code>f8</code> Build the project
6. <code>ctrl+shift+e</code> Open a <code>view</code> listing all the errors across all the files of the project
7. <code>f2</code> Click on a property, a method etc... then press <code>F2</code> to refactor it across files (Beware EXPERIMENTAL)


### Usage:

When using .sublimets or a .sublime-project file, you need to open the folder where your project is with <code>file > open folder</code> or <code>project > open project</code> in Sublime Text.
	
##### You have a sublime text project:
You can indicate your typescript root files in your project_name.sublime-project like so :
			
		
		"settings":
		{
			"typescript":
			[
				"path/from/project/folder/to/your/root/file_1.ts",
				"path/from/project/folder/to/your/root/file_2.ts",
				...
			]
		}


Exemple : 

if you have a root folder MyProject in you sublime project with a root file name root.ts inside MyProject folder 
and another folder OtherProject width a subfolder OtherSubFolder with a root file name other_root.ts inside OtherSubFolder


		"settings":
		{
			"typescript":
			[
				"MyProject/root.ts"
				"OtherProject/OtherSubFolder/other_root.ts"
			]
		}

##### You don't have a sublime text project:
You can create a .sublimets file in the folder containing the typescript root file


		{
			"root":"root_file_name.ts"
		}


If you don't chose either of these solutions the plugin wil launch a process for each file


##### Initialisation:
When you load a .ts file the plugin will initialize the root file or the current file and it can take some time for huge project.

The Sublime Text Status bar will indicate Typescript initializing during this phase and disapear when it's finished

##### Show Type:
you can click on variable or a method and press <code>F1</code> to have detail about it (doc comments etc...)

##### Got to definition:
you can click on variable or a method and press <code>F4</code> to go to the definition

##### Outline View:
you can open an <code>Outline view</code> by pressing <code>F3</code> on a file to list class variables and methods tou can then click on an item to scroll towards it

##### Auto-completion:
You can circle through the function variables (if there's some) like with the snippets with the <code>tab</code> key

##### Error highlighting: 
You can click on highlighted part to see the error description in the status bar

##### Error View: 
You have the possibility to open an <code>Error view</code> that will list all the errors accross all your project file with the command <code>ctrl+shift+e</code>
You can then click on each row, it'll open or focus the already open file concerned by the error.

##### Reloading the project:
You have the possibility to <code>reload</code> the project by pressing <code>F5</code>, you can see in the console when the reload is finished

##### Building the project:
you can build the current project with <code>F8</code> on a file. if you have activated <code>show_build_file</code> option it will show a <code>Split view</code> with the corresponding javascript file

