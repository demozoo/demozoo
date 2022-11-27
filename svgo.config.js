module.exports = {
  plugins: [
    {
      name: 'preset-default',
      params: {
        overrides: {
          // disable plugins
          removeUselessDefs: false,
          cleanupIDs: false,
        },
      },
    },
  ],
};
