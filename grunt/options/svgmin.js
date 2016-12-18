module.exports = {

    icons: {
        expand: true,
        cwd: '<%= project.dir.svg %>/icons',
        dest: '<%= project.dir.tmp %>/icons',
        src: ['*.svg']
    },

    sites: {
        expand: true,
        cwd: '<%= project.dir.svg %>/sites',
        dest: '<%= project.dir.tmp %>/icons',
        src: ['*.svg']
    }

};
