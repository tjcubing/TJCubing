var gulp = require('gulp');
var rename = require("gulp-rename");
var del = require('del');
var sass = require('gulp-sass');
var postcss = require('gulp-postcss');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var gulpIf = require('gulp-if');
var imagemin = require('gulp-imagemin');
var cache = require('gulp-cache');
var bs = require('browser-sync').create();

// https://css-tricks.com/gulp-for-beginners/

const JS = 'static/js'
const CSS = 'static/css'
const SCSS = 'src/scss'

sass.compiler = require('node-sass');

gulp.task('sass', function () {
  return gulp.src(SCSS + '/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(gulp.dest(CSS))
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
  gulp.watch(SCSS + '/*.scss', gulp.series('sass', 'css'));
}));

gulp.task('clean', function () {
  return del(['static'])
});

gulp.task('uploads', function() {
  return del(['uploads'])
});

gulp.task('clear', function (cb) {
  return cache.clearAll(cb)
})

function copyFile(name, source, destination) {
  var f = function (cb) {
    return gulp.src(source)
      .pipe(gulp.dest(destination));
    cb();
  }
  Object.defineProperty(f, "name", { value: name });
  return f
}

function copyFolder(name) {
  return copyFile(name, 'src/' + name + '/**/*', 'static/' + name)
}

gulp.task('scripts', function() {
  // Order matters apparently
  return gulp.src(['node_modules/jquery/dist/jquery.slim.min.js',
                   'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
                   'node_modules/katex/dist/katex.min.js',
                   'node_modules/feather-icons/dist/feather.min.js',
                   'node_modules/bootbox/dist/bootbox.min.js',
                   'node_modules/showdown/dist/showdown.min.js',
                   // 'node_modules/qrious/dist/qrious.min.js' 
                   // 'node_modules/katex/dist/contrib/auto-render.min.js'
                  ])
    .pipe(concat('main.min.js'))
    .pipe(gulp.dest(JS))
    .pipe(uglify())
    .pipe(gulp.dest(JS));
});

gulp.task('css', gulp.series(function() {
  return gulp.src([CSS + '/custom.css',
                   'node_modules/katex/dist/katex.min.css'
                  ])
    .pipe(concat('main.min.css'))
    .pipe(gulp.dest(CSS))
    .pipe(postcss([autoprefixer(), cssnano()]))
    .pipe(gulp.dest(CSS))
    .pipe(bs.reload({stream: true}));
}, function() {
  return del([CSS + '/custom.css'])
}));

gulp.task('img', function(){
  return gulp.src('src/img/**/*.+(png|jpg|gif|svg)')
  .pipe(cache(imagemin()))
  .pipe(gulp.dest('static/img'))
});

function defaultTask(cb) {
  // place code for your default task here
  cb();
}

var copy = gulp.parallel(copyFile('bootstrap-SCSS', 'node_modules/bootstrap/scss/**/*', SCSS + '/bootstrap'),
                         copyFile('KaTeX-fonts', 'node_modules/katex/dist/fonts/*', CSS + '/fonts'),
                         copyFile('KaTeX-auto-render', 'node_modules/katex/dist/contrib/auto-render.min.js', JS),
                         copyFile('qrious', 'node_modules/qrious/dist/qrious.min.js', JS),  
                         copyFolder('img'),
                         copyFolder('pdfs'),
                         copyFolder('misc'),
                         copyFolder('css'),
                         copyFolder('txt'),
                         copyFile('robots.txt', 'src/robots.txt', 'static'),
                         copyFile('sitemap.xml', 'src/sitemap.xml', 'static'),
                         copyFile('keybase.txt', 'src/keybase.txt', 'static'),
                         copyFile('dnt-policy.txt', 'src/dnt-policy.txt', 'static')
                        );

exports.build = gulp.series('clean', gulp.series(copy, gulp.parallel('img', 'scripts', 'sass'), 'css'))
exports.default = defaultTask;
