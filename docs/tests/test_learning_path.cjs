const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const learningPath = require('../assets/learning-path.js');
const indexHtml = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

function siteRuntimeSource() {
  const scripts = [...indexHtml.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
  const runtime = scripts
    .map((match) => match[1])
    .filter((source) => source.includes('function safeStorageRead') || source.includes('function applyLearningPathView()'));
  assert.equal(runtime.length, 2, 'docs/index.html must load storage guards before the learning-path runtime');
  return runtime.join('\n');
}

function docsifyConfigurationSource() {
  const scripts = [...indexHtml.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
  const configuration = scripts
    .map((match) => match[1])
    .find((source) => source.includes('window.$docsify ='));
  assert.ok(configuration, 'docs/index.html must expose the Docsify configuration');
  return configuration;
}

function blockedStorageBrowser() {
  const htmlClasses = new Set(['learning-path-pending']);
  const bodyClasses = new Set();
  const classList = (classes) => ({
    add: (...names) => names.forEach((name) => classes.add(name)),
    remove: (...names) => names.forEach((name) => classes.delete(name)),
    contains: (name) => classes.has(name),
    toggle: (name, force) => {
      const enabled = force === undefined ? !classes.has(name) : force;
      if (enabled) classes.add(name);
      else classes.delete(name);
      return enabled;
    },
  });
  const sandbox = {
    console,
    GoAgenticLearningPath: learningPath,
    document: {
      body: { classList: classList(bodyClasses) },
      documentElement: { classList: classList(htmlClasses), dataset: {} },
      getElementById: () => null,
      querySelector: () => null,
    },
    history: { replaceState: () => {} },
    localStorage: {
      getItem: () => { throw new Error('SecurityError: storage blocked'); },
      setItem: () => { throw new Error('SecurityError: storage blocked'); },
    },
    location: {
      hash: '#/README?id=route-systems',
      pathname: '/index.html',
      reload: () => {},
      search: '',
    },
    requestAnimationFrame: () => 1,
    addEventListener: () => {},
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(siteRuntimeSource(), sandbox);
  return { htmlClasses, sandbox };
}

test('application route contains chapters 1-16 and 23-25', () => {
  assert.deepEqual(
    learningPath.allowedChapters('application'),
    [...Array.from({ length: 16 }, (_, index) => index + 1), 23, 24, 25]
  );
});

test('full-stack route contains every chapter', () => {
  assert.deepEqual(
    learningPath.allowedChapters('fullstack'),
    Array.from({ length: 25 }, (_, index) => index + 1)
  );
});

test('systems route contains chapters 1-12 and 17-22', () => {
  assert.deepEqual(
    learningPath.allowedChapters('systems'),
    [...Array.from({ length: 12 }, (_, index) => index + 1), ...Array.from({ length: 6 }, (_, index) => index + 17)]
  );
});

test('chapter numbers are read from Chinese and English chapter links', () => {
  assert.equal(learningPath.chapterNumberFromHref('./chapter16/第十六章.md'), 16);
  assert.equal(learningPath.chapterNumberFromHref('#/en/chapter23/Chapter23-Agentic-UI.md'), 23);
  assert.equal(learningPath.chapterNumberFromHref('./appendices/附录A.md'), null);
});

test('route membership rejects chapters outside the selected route', () => {
  assert.equal(learningPath.isChapterAllowed('application', 17), false);
  assert.equal(learningPath.isChapterAllowed('application', 23), true);
  assert.equal(learningPath.isChapterAllowed('systems', 13), false);
  assert.equal(learningPath.isChapterAllowed('systems', 17), true);
});

test('adjacent chapter skips route gaps', () => {
  assert.equal(learningPath.adjacentChapter('application', 16, 1), 23);
  assert.equal(learningPath.adjacentChapter('application', 23, -1), 16);
  assert.equal(learningPath.adjacentChapter('systems', 12, 1), 17);
  assert.equal(learningPath.adjacentChapter('systems', 17, -1), 12);
  assert.equal(learningPath.adjacentChapter('systems', 22, 1), null);
});

test('route anchors override storage and invalid values fall back safely', () => {
  assert.equal(learningPath.pathFromHash('#/README?id=route-systems', 'application'), 'systems');
  assert.equal(learningPath.pathFromHash('#/chapter4/page', 'fullstack'), 'fullstack');
  assert.equal(learningPath.pathFromHash('#/chapter4/page', 'unknown'), 'application');
});

test('blocked browser storage still reveals content and keeps route operations usable', () => {
  const directStorageCalls = indexHtml.match(/localStorage\.(?:getItem|setItem)\s*\(/g) || [];
  assert.equal(directStorageCalls.length, 2, 'only the safe read/write helpers may call localStorage directly');

  const { htmlClasses, sandbox } = blockedStorageBrowser();
  const activePath = vm.runInContext('getActiveLearningPath()', sandbox);
  assert.equal(activePath, 'systems');
  assert.doesNotThrow(() => vm.runInContext('applyLearningPathView()', sandbox));
  assert.equal(sandbox.document.documentElement.dataset.learningPath, 'systems');
  assert.equal(htmlClasses.has('learning-path-pending'), false);

  sandbox.location.hash = '#/chapter4/page';
  assert.equal(vm.runInContext('getActiveLearningPath()', sandbox), 'application');
});

test('browser-rendered Mermaid SVG exposes an accessible title and description', async () => {
  const attributes = {};
  const svg = {
    querySelector: (selector) => ({
      id: selector === 'title' ? 'chart-title-test' : 'chart-desc-test',
    }),
    setAttribute: (name, value) => { attributes[name] = value; },
  };
  const diagram = { querySelector: (selector) => selector === 'svg' ? svg : null };
  let doneEach;
  const sandbox = {
    console,
    document: {
      querySelector: () => null,
      querySelectorAll: (selector) => selector === '.mermaid' ? [diagram] : [],
    },
    mermaid: { run: () => Promise.resolve() },
    requestAnimationFrame: () => 1,
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(docsifyConfigurationSource(), sandbox);
  sandbox.$docsify.plugins[0]({
    doneEach: (callback) => { doneEach = callback; },
  });

  doneEach();
  await new Promise((resolve) => setImmediate(resolve));

  assert.equal(attributes['aria-labelledby'], 'chart-title-test');
  assert.equal(attributes['aria-describedby'], 'chart-desc-test');
});
