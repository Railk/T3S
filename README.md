TSS Sublime (T3S)
----------------------------------------------------------------------------

Typescript plugin for sublime text 2 and 3 using Typescript tools (Tss).

I'm using the same error icons has SublimeLinter.

I took inspiration from : https://github.com/raph-amiard/sublime-typescript


### Feature :
1. TypeScript language auto completion
2. TypeScript language error highlighting
3. TypeScript language syntax highlighting


### Dependencies :
1. nodejs
2. tss https://github.com/clausreinke/typescript-tools and tss must be in your environnement path

### OS
Tested on Windows & Ubuntu & OSX

### Problem
OSX has currently the path for node and tss hardcoded (default installation directory) du to some environnment PATH for GUI app problem.


### Installation Sublime Text 3 :

##### Sublime text Package directory :
Click the Preferences > Browse Packages… menu


##### Without Git : 
Download the latest source zip from github and extract the files to your Sublime Text "Packages" directory, into a new directory named Typescript.

##### With Git : 
Clone the repository in your Sublime Text "Packages" directory.


### Installation Sublime Text 2 :

##### Sublime text Package directory :
Click the Preferences > Browse Packages… menu


##### Without Git : 
1. Choose ST2 Branch
2. Download the latest source zip from github and extract the files to your Sublime Text "Packages" directory, into a new directory named Typescript.

##### With Git : 
1. Clone the repository in your Sublime Text "Packages" directory.
2. Git checkout ST2 branch



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