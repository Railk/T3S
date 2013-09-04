TSS Sublime (T3S)
----------------------------------------------------------------------------

Typescript plugin for sublime text 2 and 3 using Typescript tools ( https://github.com/clausreinke/typescript-tools )

I'm using the same error icons has SublimeLinter.

I took inspiration from : https://github.com/raph-amiard/sublime-typescript


### Feature :
1. TypeScript language auto completion
2. TypeScript language error highlighting
3. TypeScript language syntax highlighting
4. A build System


### Dependencies :
1. nodejs
2. tss (https://github.com/clausreinke/typescript-tools) if you set local_tss to false in settings
3. tsc for the build system that you install via <code>npm install -g typescript</code> (http://www.typescriptlang.org/)


### OS
Tested on Windows & Ubuntu & OSX

### Problem
OSX has currently the path for node hardcoded (default installation directory) du to some environnment PATH for GUI app problem.

### Installation Sublime Text 3 :

##### Sublime text Package directory :
Click the Preferences > Browse Packages… menu


##### Without Git : 
Download the latest source zip from github and extract the files to your Sublime Text "Packages" directory, into a new directory named <code>T3S</code>.

##### With Git : 
Clone the repository in your Sublime Text "Packages" directory.


### Installation Sublime Text 2 :

##### Sublime text Package directory :
Click the Preferences > Browse Packages… menu


##### Without Git : 
1. Choose ST2 Branch
2. Download the latest source zip from github and extract the files to your Sublime Text "Packages" directory, into a new directory named <code>T3S</code>.

##### With Git : 
1. Clone the repository in your Sublime Text "Packages" directory.
2. Git checkout ST2 branch


### Settings:
You have two settings available :

1. local_tss : to use the local tss or the command line TSS, the default is using the local_tss
2. error_on_save_only : to highlight errors only while saving or while typing, the default is showing error highlighting while typing
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
				"skip_resolution_and preprocessing":false,
				"remove_comments_from_output":false,
				"generate_source_map":false,
				"ecmascript_target":"ES3"
			}
		}


##### local_tss :
the plugin use a local version of tss situated in the bin folder as seen in Typescript.sublime-settings file:

		
		"local_tss":true
		
		

You can use the tss command line tool (check installation method on the tss page) by setting local_tss to false, but with so the plugin will be perhaps behind TSS in terms of update and it could make the plugin not working is there's some api change.

		
		"local_tss":false
		
		

##### error_on_save_only :
Error highlighting while typing (will lag a bit du to calculation and this cannot be changed) :

		
		"error_on_save_only":false
		

Error highlighting only shown when saving :

		
		"error_on_save_only":true


##### build_parameters :
I've added a build system that take most of the command line parameters of TSC, i'll not explain them here, you can install TSC and look at the parameters via <code>tsc -h</code>

And you also have two extra parameters that are <code>pre_processing_commans</code> and <code>post_processing_commans</code> that gave you the opportunities to do command line things before and after <code>tsc</code> compiling

These are the default values :
		
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
				"skip_resolution_and preprocessing":false,
				"remove_comments_from_output":false,
				"generate_source_map":false,
				"ecmascript_target":"ES3"
			}
		}



### Usage:
	
##### You have a sublime text project :
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
		

##### You don't have a sublime text project :
You can create a .sublimets file in the folder containing the typescript root file


		{
			"root":"root_file_name.ts"
		}


If you don't chose either of these solutions the plugin wil launch a process for each file


##### Initialisation :
When you load a .ts file the plugin will initialize the root file or the current file and it can take some time for huge project.

The Sublime Text Status bar will indicate Typescript initializing during this phase and disapear when it's finished


##### Error highlighting : 
You can click on highlighted part to see the error description in the status bar