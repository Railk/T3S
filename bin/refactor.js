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

var output = "";

// REPLACE
for (var i = 0; i < refs.length; i++) {
	var path = refs[i].ref.fileName;
	var index = refs[i].ref.minChar;
	var size = refs[i].ref.limChar-refs[i].ref.minChar;

	var out = fs.readFileSync(path, FILE_ENCODING).replaceAt(index,size,replace);
	fs.writeFileSync(path, out, FILE_ENCODING);

	lines = out.split('\n').length;
	console.log(encode({"file": {"content":out,"lines":lines,"filename":path} }));
	output += '\n'+path+' ('+lines+')';
}

console.log(encode({"output":"Typescript refactor finished, the following files have been modified :\n"+ output}));