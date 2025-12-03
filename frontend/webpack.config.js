const path = require('path');
module.exports = {
  entry: './src/index.jsx',
  output: { path: path.resolve(__dirname, 'dist'), filename: 'bundle.js', publicPath: '/' },
  devServer: {
    static: path.join(__dirname, 'public'),
    historyApiFallback: true,
    port: 3000,
    proxy: { '/api': 'http://localhost:8000', '/ws': { target: 'ws://localhost:8000', ws: true } }
  },
  module: {
    rules: [
      { test: /\.jsx?$/, exclude: /node_modules/, use: { loader: 'babel-loader' } },
      { test: /\.css$/, use: ['style-loader','css-loader'] },
    ]
  },
  resolve: { extensions: ['.js','.jsx'] }
};
