// IMPORT
var fs = require('fs'),
	path = require('path'),
	cmd = require('child_process').exec;


// VARS
var FILE_ENCODING = 'utf-8';
var EOL = '[end]';

var config = JSON.parse(process.argv[2]);
var filename = process.argv[3];
var js_file = process.argv[4];
var directory = path.dirname(filename);

var commands_map = {
	"output_dir_path":"--outDir ",
	"concatenate_and_emit_output_file_path":"--out ",
	"source_files_root_path":"--sourceRoot ",
	"map_files_root_path":"--mapRoot ",
	"module_kind":"--module ",
	"allow_bool_synonym":"--allowbool",
	"allow_import_module_synonym":"--allowimportmodule",
	"generate_declaration":"--declaration",
	"no_implicit_any_warning":"--noImplicitAny",
	"skip_resolution_and_preprocessing":"--noResolve",
	"remove_comments_from_output":"--removeComments",
	"generate_source_map":"--sourcemap",
	"ecmascript_target":"--target "
};

var default_values = {
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
};


////////////////////////////////////////////////////////////////////////////////////////
process.chdir(directory);

function build_commands(){
	var tsc = "";
	var commands = [];

	for (var option in config){
		if(default_values[option] != config[option] && option!=='pre_processing_commands' && option!=='post_processing_commands') {
			tsc += ' '+commands_map[option]+(default_values[option]!==false?config[option]:'');
		}
	}


	var i,
		pre_processing_commands = config['pre_processing_commands'],
		post_processing_commands = config['post_processing_commands'];

	for (i = 0; i < pre_processing_commands.length; i++) {
		commands[commands.length] = pre_processing_commands[i];
	}

<<<<<<< HEAD:bin/build.js
	if(process.platform === 'darwin'){
		if(process.env.PATH.indexOf(':/usr/local/bin') === -1){
			process.env.PATH += ':/usr/local/bin';
		}
	}
=======
>>>>>>> master:Typescript.build.js
	commands[commands.length] = 'tsc '+'"'+filename+'"'+tsc;

	for (i = 0; i < post_processing_commands.length; i++) {
		commands[commands.length] =post_processing_commands[i];
	}

	return commands;
}


var commands = build_commands();
var num_commands = commands.length;
var index = 0;
var error = "";
var output = "";

function encode(message){
	return JSON.stringify(message);
}

function end(built){
	var file = path.join(directory,config["output_dir_path"],js_file);
	
	if(error!=="") console.log(encode({'output':EOL+"ERRORS : "+EOL+EOL+error}));

	if(built) console.log(encode({'filename':file}));
	else console.log(encode({'filename':'error'}));
}

function exec(index){
	console.log(encode({'output':'executing command : '+commands[index]+EOL}));
	cmd(commands[index],function(err,stdout,stderr){
		if(stdout!==null && stdout!=='') console.log(encode({'output':stdout.replace(/[\n]/g,EOL)+EOL}));
		if(stderr!==null && stderr!==''){
			error += stderr.replace(/[\n]/g,EOL)+EOL;
			end(false);
			return;
		}
		if(index+1<num_commands) exec(index+1);
		else end(true);
	});
}

console.log(encode({'output':'T3S building ... '+commands+EOL}));
exec(0);

////////////////////////////////////////////////////////////////////////////////////////