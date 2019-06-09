const { series, parallel, src, dest } = require('gulp');

const JS = 'static/js'
const CSS = 'static/css'

function defaultTask(cb) {
  // place code for your default task here
  cb();
}

function copyFile(name, source, destination) {
  var f = function (cb) {
    return src(source)
      .pipe(dest(destination));
    cb();
  }
  Object.defineProperty(f, "name", { value: name });
  return f
}

exports.build = parallel(copyFile('bootstrap-JS', 'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js', JS),
                         copyFile('bootstrap-CSS', 'node_modules/bootstrap/dist/css/bootstrap.min.css', CSS),
                         copyFile('bootstrap-SCSS', 'node_modules/bootstrap/scss/**/*', 'static/scss/bootstrap'),
                         copyFile('KaTeX-JS', 'node_modules/katex/dist/katex.min.js', JS),
                         copyFile('KaTeX-CSS', 'node_modules/katex/dist/katex.min.css', CSS),
                         copyFile('KaTeX-fonts', 'node_modules/katex/dist/fonts/*', 'static/css/fonts'),
                         copyFile('KaTeX-auto-render', 'node_modules/katex/dist/contrib/auto-render.min.js', JS),
                         copyFile('jQuery', 'node_modules/jquery/dist/jquery.slim.min.js', JS),
                        )
exports.default = defaultTask
