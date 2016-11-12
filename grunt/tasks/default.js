module.exports = function (grunt) {

    grunt.registerTask('default', [
        'clean:tmp',
        'svgmin',
        'svgstore'
    ]);
};
