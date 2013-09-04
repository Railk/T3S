// IMPORT
var fs = require('fs'),
	cmd = require('child_process').exec,
	_path = require("path");


// VARS
var FILE_ENCODING = 'utf-8';
var EOL = '\n';

var config_file = process.argv[2];
var filename = process.argv[3];

var commands = {
	"output_dir_path":"--outDir ",
	"concatenate_and_emit_output_file_path":"--out ",
	"source_files_root_path":"--sourceRoot ",
	"map_files_root_path":"--mapRoot ",
	"module_kind":"--module ",
	"allow_bool_synonym":"--allowbool",
	"allow_import_module_synonym":"--allowimportmodule",
	"generate_declaration":"--declaration",
	"no_implicit_any_warning":"--noImplicitAny",
	"skip_resolution_and preprocessing":"--noResolve",
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
	"skip_resolution_and preprocessing":false,
	"remove_comments_from_output":false,
	"generate_source_map":false,
	"ecmascript_target":"ES3"
};


////////////////////////////////////////////////////////////////////////////////////////

var config =  JSON.parse(fs.readFileSync(config_file, FILE_ENCODING));

function build_command(){
	var command = "";
	for (var option in config){
		if(default_values[option] != config[option]) {
			command += ' '+commands[option]+(default_values[option]!==false?config[option]:'');
		}
	}
	return command;
}


var command = build_command();
console.log('TSC compiling ... tsc '+filename+command);
cmd('tsc '+filename+build_command(),function(err,stdout,stderr){
	if(stdout!==null) console.log(stdout);
	if(stderr!==null) console.log(stderr);
});


////////////////////////////////////////////////////////////////////////////////////////