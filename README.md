TSS Sublime (T3S)
----------------------------------------------------------------------------

TypeScript plugin for Sublime Text 2 and 3 using TypeScript tools ( https://github.com/clausreinke/typescript-tools )

I'm using the same error icons has SublimeLinter.

I took inspiration from: https://github.com/raph-amiard/sublime-typescript


### Features
- TypeScript language auto completion
- TypeScript language error highlighting
- TypeScript language syntax highlighting
- A build System


### Dependencies
- node.js
- tss (https://github.com/clausreinke/typescript-tools) if you set local_tss to false in settings
- tsc for the build system that you install via <code>npm install -g typescript</code> (http://www.typescriptlang.org/)


### OS
Tested on Windows & Ubuntu & OSX

### Problem
OSX has currently the path for node hardcoded (default installation directory) du to some environnment <code>PATH</code> for GUI app problem.

### Installation for Sublime Text 3:

##### Sublime text Package directory:
Click the <code>Preferences > Browse Packages…</code> menu


##### Without Git: 
Download the latest source zip from github and extract the files to your Sublime Text <code>Packages</code> directory, into a new directory named <code>T3S</code>.

##### With Git:
Clone the repository in your Sublime Text <code>Packages</code> directory.


### Installation for Sublime Text 2:

##### Sublime text Package directory:
Click the <code>Preferences > Browse Packages…</code> menu


##### Without Git:
1. Choose ST2 Branch
2. Download the latest source zip from github and extract the files to your Sublime Text <code>Packages</code> directory, into a new directory named <code>T3S</code>.

##### With Git:
1. Clone the repository in your Sublime Text <code>Packages</code> directory.
2. Checkout ST2 branch using <code>git checkout st2</code>.


### Settings:
You can acces the plugin settings from <code>Preferences > Packages Settings > T3S</code>, to modify the settings please copy the default settings inside the user settings one, and make your modification there otherwise your settings will be override by an update of the plugin.

You have 3 settings available:

1. <code>local_tss</code>: to use the local tss or the command line TSS, the default is using the local_tss
2. <code>error_on_save_only</code>: to highlight errors only while saving or while typing, the default is showing error highlighting while typing
3. the build parameters


		{
			"local_tss":true,
			"error_on_save_only":false,

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


##### local_tss:
the plugin use a local version of tss situated in the bin folder :

		
		"local_tss":true
		
		

You can use the tss command line tool (check installation method on the tss page) by setting local_tss to false, but with so the plugin will be perhaps behind TSS in terms of update and it could make the plugin not working is there's some api change.

		
		"local_tss":false
		
		

##### error_on_save_only:
Error highlighting while typing (will lag a bit du to calculation and this cannot be changed):

		
		"error_on_save_only":false
		

Error highlighting only shown when saving:

		
		"error_on_save_only":true


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


### Usage:
	
##### You have a sublime text project:
You can indicate your typescript root files in your project_name.sublime-project like so :
			
		
		"settings":
		{
			"typescript":
			[
				"absolute/path/to/your/root/file_1.ts",
				"absolute/path/to/your/root/file_2.ts",
				...
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

##### Auto-completion:
You can circle through the function variables (if there's some) like with the snippets with the <code>tab</code> key

##### Error highlighting: 
You can click on highlighted part to see the error description in the status bar


##### Error Panel: 
You have the possibility to open an <code>error panel</code> that will list all the errors accross all your project file with the command <code>ctrl+shift+e</code>
You can then click on each row, it'll open or focus the already open file concerned by the error.
