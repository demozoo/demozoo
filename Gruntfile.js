var path = require("path");

/**
 *
 * @param grunt
 */
module.exports = function (grunt) {

    function loadConfig(path) {
        var glob = require('glob');
        var object = {};
        var key;

        glob.sync('*', {cwd: path}).forEach(function (option) {
            key = option.replace(/\.js$/, '');
            object[key] = require(path + option);
        });

        return object;
    }

    var config = {
        pkg: grunt.file.readJSON('package.json'),
        env: process.env,
        project: grunt.file.readJSON('./grunt/config.json')
    };

    // Required load-grunt-tasks
    require('load-grunt-tasks')(grunt);

    // Load tasks
    grunt.loadTasks('./grunt/tasks/');

    // Load options
    grunt.util._.extend(config, loadConfig('./grunt/options/'));

    // Run concatenated tasks and options
    grunt.initConfig(config);
};
