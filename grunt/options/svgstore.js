module.exports = {

    options: {
        cleanupdefs: true,
        includedemo: false,
        prefix: "icon--",
        svg: {
            xmlns: 'http://www.w3.org/2000/svg'
        }
    },

    icons: {
        files: {
            '<%= project.dir.static %>/images/icons.svg': '<%= project.dir.tmp %>/icons/*.svg'
        }
    },

    sites: {
        files: {
            '<%= project.dir.static %>/images/sites.svg': '<%= project.dir.tmp %>/sites/*.svg'
        }
    }


};
