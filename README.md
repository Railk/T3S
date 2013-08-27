TSS Sublime (T3S)
----------------------------------------------------------------------------

Typescript plugin for sublime text 2 and 3 using Typescript tools (Tss)


### Feature :
1. TypeScript language auto completion
2. TypeScript language error highlighting


### Dependencies :
1. nodejs
2. tss https://github.com/clausreinke/typescript-tools and tss must be in your environnement path

### OS
Tested on windows only for the moment

### Todo
check on Linux and OSX version of Sublime Text

### Installation Sublime Text 3 :

#### Sublime text Package directory :
Click the Preferences > Browse Packages… menu


#### Without Git : 
Download the latest source zip from github and extract the files to your Sublime Text "Packages" directory, into a new directory named Typescript.

#### With Git : 
Clone the repository in your Sublime Text "Packages" directory.


### Usage:
	
##### You have a sublime text project :
You can indicate your typescript root files in your project_name.sublime-project like so :
			
		
		"settings":
		{
			"typescript":
			[
				"path/to/your/root/file_1",
				"path/to/your/root/file_2",
				...
			]
		}
		

##### You don't have a sublime text project :
You can create a .sublimets file in the folder containing the typescript root file


		{
			"root":"root_file_name.ts"
		}


If you don't chose either of these solutions the plugin wil launch a process for each file