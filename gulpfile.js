var gulp = require('gulp');
var sass = require('gulp-sass');
var postcss = require('gulp-postcss');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var bs = require('browser-sync').create();

// TODO: concat, minify, image compression

const JS = 'static/js'
const CSS = 'static/css'
const SCSS = 'static/scss'

sass.compiler = require('node-sass');

gulp.task('sass', function () {
  return gulp.src(SCSS + '/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss([autoprefixer(), cssnano()]))
    .pipe(gulp.dest(CSS))
    .pipe(bs.reload({stream: true}));
});

gulp.task('browser-sync', function() {
    bs.init({
        port: 3000,
        proxy: {
          target: "localhost:5000"
        }
    });
});

gulp.task('watch', gulp.parallel('browser-sync', function () {
  gulp.watch(SCSS + '/*.scss', gulp.series('sass'));
}));

function defaultTask(cb) {
  // place code for your default task here
  cb();
}

function copyFile(name, source, destination) {
  var f = function (cb) {
    return gulp.src(source)
      .pipe(gulp.dest(destination));
    cb();
  }
  Object.defineProperty(f, "name", { value: name });
  return f
}

exports.copy = gulp.parallel(copyFile('bootstrap-JS', 'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js', JS),
                             copyFile('bootstrap-CSS', 'node_modules/bootstrap/dist/css/bootstrap.min.css', CSS),
                             copyFile('bootstrap-SCSS', 'node_modules/bootstrap/scss/**/*', 'static/scss/bootstrap'),
                             copyFile('KaTeX-JS', 'node_modules/katex/dist/katex.min.js', JS),
                             copyFile('KaTeX-CSS', 'node_modules/katex/dist/katex.min.css', CSS),
                             copyFile('KaTeX-fonts', 'node_modules/katex/dist/fonts/*', 'static/css/fonts'),
                             copyFile('KaTeX-auto-render', 'node_modules/katex/dist/contrib/auto-render.min.js', JS),
                             copyFile('jQuery', 'node_modules/jquery/dist/jquery.slim.min.js', JS),
                            )
exports.default = defaultTask
