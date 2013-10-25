// IMPORT
var fs = require('fs');


// VARS
var FILE_ENCODING = 'utf-8';
var replace = process.argv[2];
var refs = JSON.parse(process.argv[3]);

// STRING REPLACE AT
String.prototype.replaceAt=function(index,length, str) {
    return this.substr(0, index) + str + this.substr(index+length);
};

function encode(message){
	return JSON.stringify(message);
}

function get_chars(out,num_lines){
	lines = out.split('\n');
	chars = 0;
	for (var i = 0; i < num_lines-1; i++) {
		chars += lines[i].length+1;
	}
	return chars;
}

var output = "";

// REPLACE
for (var i = 0; i < refs.length; i++) {
	var path = refs[i].ref.fileName;
	var out = fs.readFileSync(path, FILE_ENCODING);
	var index = get_chars(out,refs[i]['min']['line']) + refs[i]['min']['character']-1;
	var end = refs[i]['lim']['character'] - refs[i]['min']['character'];
	out = out.replaceAt(index,end,replace);
	fs.writeFileSync(path, out, FILE_ENCODING);

	console.log(encode({"file":path}));
	output += '\n'+path+' ('+index+','+end+')';
}

console.log(encode({"output":"Typescript refactor finished, the following files have been modified :\n"+ output}));