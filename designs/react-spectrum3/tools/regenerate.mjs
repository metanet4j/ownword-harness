import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const groups = [
  {
    slug: 'actions',
    title: 'Actions',
    subtitle: 'Buttons, grouped actions, and direct manipulation triggers.',
    components: ['ActionBar', 'ActionBarContainer', 'ActionButton', 'ActionGroup', 'ActionMenu', 'Button', 'ButtonGroup', 'FileTrigger', 'LogicButton', 'ToggleButton']
  },
  {
    slug: 'forms',
    title: 'Forms',
    subtitle: 'Input, selection, validation, and form composition controls.',
    components: ['Checkbox', 'CheckboxGroup', 'ComboBox', 'DropZone', 'Form', 'NumberField', 'Picker', 'Radio', 'RadioGroup', 'RangeSlider', 'SearchField', 'Slider', 'Switch', 'TextArea', 'TextField']
  },
  {
    slug: 'date-time',
    title: 'Date and time',
    subtitle: 'Calendar, date, range, and time entry families.',
    components: ['Calendar', 'DateField', 'DatePicker', 'DateRangePicker', 'RangeCalendar', 'TimeField']
  },
  {
    slug: 'color',
    title: 'Color',
    subtitle: 'Color editing, sampling, and spatial controls.',
    components: ['ColorArea', 'ColorEditor', 'ColorField', 'ColorPicker', 'ColorSlider', 'ColorSwatch', 'ColorSwatchPicker', 'ColorWheel']
  },
  {
    slug: 'content-layout',
    title: 'Content and layout',
    subtitle: 'Typography, media, status, theming, and layout primitives.',
    components: ['Avatar', 'Badge', 'Content', 'Divider', 'Flex', 'Footer', 'Grid', 'Header', 'Heading', 'Icon', 'IllustratedMessage', 'Image', 'Keyboard', 'LabeledValue', 'Link', 'Provider', 'SSRProvider', 'StatusLight', 'Text', 'View', 'VisuallyHidden', 'Well']
  },
  {
    slug: 'collections-navigation',
    title: 'Collections and navigation',
    subtitle: 'Structured collections, disclosure, tabs, tables, and trees.',
    components: ['Accordion', 'Breadcrumbs', 'Cell', 'Collection', 'Column', 'Disclosure', 'DisclosurePanel', 'DisclosureTitle', 'Item', 'ListBox', 'ListView', 'Row', 'Section', 'TabList', 'TabPanels', 'Tabs', 'TableBody', 'TableHeader', 'TableView', 'TagGroup', 'TreeView', 'TreeViewItem', 'TreeViewItemContent']
  },
  {
    slug: 'feedback-overlays',
    title: 'Feedback and overlays',
    subtitle: 'Dialogs, contextual surfaces, progress, notifications, and menus.',
    components: ['AlertDialog', 'ContextualHelp', 'ContextualHelpTrigger', 'Dialog', 'DialogContainer', 'DialogTrigger', 'InlineAlert', 'Menu', 'MenuTrigger', 'Meter', 'ProgressBar', 'ProgressCircle', 'SubmenuTrigger', 'ToastContainer', 'ToastQueue', 'Tooltip', 'TooltipTrigger']
  }
];

const allComponents = groups.flatMap(group => group.components);
const uniqueComponents = new Set(allComponents);
if (allComponents.length !== 101 || uniqueComponents.size !== allComponents.length) {
  throw new Error(`Expected 101 unique public visual exports, found ${allComponents.length}/${uniqueComponents.size}.`);
}

function write(relativePath, content) {
  const output = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(output), {recursive: true});
  fs.writeFileSync(output, content.replace(/\r\n/g, '\n'), 'utf8');
}

function humanize(value) {
  return value.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
}

function componentSource(name) {
  return `import {renderSpectrumComponent} from '../shared/spectrumPrimitive.jsx';

export function ${name}(props) {
  return renderSpectrumComponent('${name}', props);
}
`;
}

function componentTypes(name) {
  return `import type {ReactElement, ReactNode} from 'react';

export interface ${name}Props {
  children?: ReactNode;
  label?: string;
  description?: string;
  value?: string | number;
  variant?: 'accent' | 'primary' | 'secondary' | 'negative' | 'quiet';
  size?: 'S' | 'M' | 'L';
  isDisabled?: boolean;
  isSelected?: boolean;
  isQuiet?: boolean;
  onPress?: () => void;
  className?: string;
  'aria-label'?: string;
}

export declare function ${name}(props: ${name}Props): ReactElement;
`;
}

function componentPrompt(name, group) {
  return `${name} recreates the React Spectrum 3 ${humanize(name).toLowerCase()} visual family for ${group.title.toLowerCase()} mockups.

\`\`\`jsx
<${name} label="${humanize(name)}" />
\`\`\`

Use Spectrum labels, compact density, visible focus, and disabled states. This design component is a cosmetic prototype surface; production accessibility and behavior belong to \`@adobe/react-spectrum\`.
`;
}

const primitiveSource = `import React from 'react';

const buttonKinds = new Set(['ActionButton', 'ActionMenu', 'Button', 'FileTrigger', 'LogicButton', 'MenuTrigger', 'SubmenuTrigger', 'ToggleButton', 'TooltipTrigger', 'ContextualHelpTrigger', 'DialogTrigger']);
const fieldKinds = new Set(['ColorField', 'ComboBox', 'DateField', 'DatePicker', 'DateRangePicker', 'NumberField', 'Picker', 'SearchField', 'TextField', 'TimeField']);
const calendarKinds = new Set(['Calendar', 'RangeCalendar']);
const collectionKinds = new Set(['Accordion', 'Breadcrumbs', 'Collection', 'ListBox', 'ListView', 'Menu', 'TableBody', 'TableHeader', 'TableView', 'TagGroup', 'TreeView']);
const overlayKinds = new Set(['AlertDialog', 'ContextualHelp', 'Dialog', 'DialogContainer', 'InlineAlert', 'ToastContainer', 'ToastQueue', 'Tooltip']);

function labelFor(kind, props) {
  return props.children || props.label || kind.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
}

function calendar(kind, props) {
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S', '29', '30', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
  return React.createElement('section', {className: 'rsp3-calendar', 'aria-label': props['aria-label'] || kind},
    React.createElement('header', null, React.createElement('button', {type: 'button'}, '‹'), React.createElement('strong', null, kind === 'RangeCalendar' ? 'April – May 2026' : 'April 2026'), React.createElement('button', {type: 'button'}, '›')),
    React.createElement('div', {className: 'rsp3-calendar-grid'}, days.map((day, index) => React.createElement('span', {className: index === 12 ? 'is-selected' : index < 7 ? 'is-weekday' : '', key: index}, day)))
  );
}

function collection(kind, props) {
  const label = labelFor(kind, props);
  if (kind === 'Breadcrumbs') {
    return React.createElement('nav', {className: 'rsp3-breadcrumbs'}, React.createElement('a', {href: '#'}, 'Home'), React.createElement('span', null, '/'), React.createElement('a', {href: '#'}, 'Assets'), React.createElement('span', null, '/'), React.createElement('strong', null, 'Current'));
  }
  if (kind === 'Accordion') {
    return React.createElement('div', {className: 'rsp3-accordion'}, React.createElement('div', null, '▾  Details'), React.createElement('p', null, 'Expanded Spectrum content.'));
  }
  if (kind === 'TableView' || kind === 'TableHeader' || kind === 'TableBody') {
    return React.createElement('table', {className: 'rsp3-table'}, React.createElement('thead', null, React.createElement('tr', null, React.createElement('th', null, 'Name'), React.createElement('th', null, 'Status'))), React.createElement('tbody', null, React.createElement('tr', null, React.createElement('td', null, 'Asset.psd'), React.createElement('td', null, 'Ready')), React.createElement('tr', null, React.createElement('td', null, 'Review.pdf'), React.createElement('td', null, 'Shared'))));
  }
  return React.createElement('section', {className: 'rsp3-collection'}, React.createElement('strong', null, label), React.createElement('div', {className: 'is-selected'}, 'Selected item'), React.createElement('div', null, 'Second item'), React.createElement('div', null, 'Third item'));
}

function overlay(kind, props) {
  return React.createElement('section', {className: 'rsp3-overlay'}, React.createElement('strong', null, labelFor(kind, props)), React.createElement('p', null, props.description || 'Clear, concise supporting message.'), React.createElement('div', {className: 'rsp3-inline-actions'}, React.createElement('button', {className: 'rsp3-button rsp3-button-secondary', type: 'button'}, 'Cancel'), React.createElement('button', {className: 'rsp3-button rsp3-button-accent', type: 'button'}, 'Confirm')));
}

export function renderSpectrumComponent(kind, props = {}) {
  const label = labelFor(kind, props);
  const disabled = Boolean(props.isDisabled);
  const press = props.onPress;

  if (buttonKinds.has(kind)) {
    const variant = props.variant || (kind === 'Button' ? 'accent' : 'secondary');
    return React.createElement('button', {className: \`rsp3-button rsp3-button-\${variant}\`, disabled, onClick: press, type: 'button'}, label);
  }
  if (kind === 'ActionBar' || kind === 'ActionBarContainer' || kind === 'ActionGroup' || kind === 'ButtonGroup') {
    return React.createElement('div', {className: 'rsp3-inline-actions'}, React.createElement('button', {className: 'rsp3-button rsp3-button-secondary', type: 'button'}, 'Edit'), React.createElement('button', {className: 'rsp3-button rsp3-button-secondary', type: 'button'}, 'Share'), React.createElement('button', {className: 'rsp3-button rsp3-button-quiet', type: 'button'}, 'More'));
  }
  if (kind === 'Checkbox' || kind === 'Radio' || kind === 'Switch') {
    const inputType = kind === 'Radio' ? 'radio' : 'checkbox';
    return React.createElement('label', {className: \`rsp3-choice rsp3-choice-\${kind.toLowerCase()}\`}, React.createElement('input', {type: inputType, defaultChecked: props.isSelected !== false, disabled}), React.createElement('span', null), React.createElement('b', null, label));
  }
  if (kind === 'CheckboxGroup' || kind === 'RadioGroup') {
    const inputType = kind === 'RadioGroup' ? 'radio' : 'checkbox';
    return React.createElement('fieldset', {className: 'rsp3-choice-group'}, React.createElement('legend', null, label), ['First option', 'Second option'].map((item, index) => React.createElement('label', {className: 'rsp3-choice', key: item}, React.createElement('input', {type: inputType, name: kind, defaultChecked: index === 0}), React.createElement('span', null), React.createElement('b', null, item))));
  }
  if (fieldKinds.has(kind)) {
    const fieldType = kind === 'SearchField' ? 'search' : kind === 'NumberField' ? 'number' : 'text';
    return React.createElement('label', {className: 'rsp3-field'}, React.createElement('span', null, label), React.createElement('div', {className: 'rsp3-field-shell'}, React.createElement('input', {type: fieldType, defaultValue: props.value || (kind.includes('Date') ? 'Apr 15, 2026' : 'Spectrum value'), disabled}), React.createElement('button', {type: 'button', tabIndex: -1}, kind === 'SearchField' ? '×' : '⌄')));
  }
  if (kind === 'TextArea') {
    return React.createElement('label', {className: 'rsp3-field'}, React.createElement('span', null, label), React.createElement('textarea', {defaultValue: props.value || 'Write a clear description.', disabled}));
  }
  if (kind === 'Form') {
    return React.createElement('form', {className: 'rsp3-form'}, React.createElement('label', {className: 'rsp3-field'}, React.createElement('span', null, 'Project name'), React.createElement('input', {defaultValue: 'Spectrum project'})), React.createElement('label', {className: 'rsp3-choice'}, React.createElement('input', {type: 'checkbox', defaultChecked: true}), React.createElement('span', null), React.createElement('b', null, 'Send updates')), React.createElement('button', {className: 'rsp3-button rsp3-button-accent', type: 'button'}, 'Save'));
  }
  if (kind === 'DropZone') {
    return React.createElement('div', {className: 'rsp3-dropzone'}, React.createElement('strong', null, 'Drop files here'), React.createElement('span', null, 'or choose from your computer'));
  }
  if (kind === 'Slider' || kind === 'RangeSlider') {
    return React.createElement('label', {className: 'rsp3-slider'}, React.createElement('span', null, label), React.createElement('input', {type: 'range', min: 0, max: 100, defaultValue: kind === 'RangeSlider' ? 64 : 42}));
  }
  if (calendarKinds.has(kind)) {
    return calendar(kind, props);
  }
  if (kind.startsWith('Color')) {
    if (kind === 'ColorSwatch') {
      return React.createElement('div', {className: 'rsp3-color-swatch', title: '#0265DC'});
    }
    if (kind === 'ColorSwatchPicker') {
      return React.createElement('div', {className: 'rsp3-swatches'}, ['#0265dc', '#d31510', '#007a4d', '#b14c00', '#5c5ce0'].map(color => React.createElement('button', {key: color, style: {background: color}, title: color, type: 'button'})));
    }
    return React.createElement('section', {className: \`rsp3-color-control rsp3-color-\${kind.toLowerCase()}\`}, React.createElement('div', null), React.createElement('code', null, '#0265DC'));
  }
  if (kind === 'ProgressBar' || kind === 'Meter') {
    return React.createElement('label', {className: 'rsp3-progress'}, React.createElement('span', null, label, ' · 64%'), React.createElement('progress', {max: 100, value: 64}));
  }
  if (kind === 'ProgressCircle') {
    return React.createElement('div', {className: 'rsp3-progress-circle'}, React.createElement('span', null, '64'));
  }
  if (kind === 'StatusLight') {
    return React.createElement('span', {className: 'rsp3-status'}, React.createElement('i', null), label);
  }
  if (kind === 'Badge') {
    return React.createElement('span', {className: 'rsp3-badge'}, label);
  }
  if (kind === 'Avatar') {
    return React.createElement('div', {className: 'rsp3-avatar', 'aria-label': props['aria-label'] || 'Avatar'}, 'RS');
  }
  if (kind === 'Divider') {
    return React.createElement('hr', {className: 'rsp3-divider'});
  }
  if (kind === 'Heading') {
    return React.createElement('h3', {className: 'rsp3-heading'}, label);
  }
  if (kind === 'Text') {
    return React.createElement('p', {className: 'rsp3-text'}, label);
  }
  if (kind === 'Keyboard') {
    return React.createElement('kbd', {className: 'rsp3-keyboard'}, '⌘ K');
  }
  if (kind === 'Link') {
    return React.createElement('a', {className: 'rsp3-link', href: '#'}, label);
  }
  if (kind === 'Image' || kind === 'IllustratedMessage') {
    return React.createElement('div', {className: 'rsp3-media'}, React.createElement('div', {className: 'rsp3-media-shape'}, kind === 'Image' ? 'Image' : '!'), React.createElement('strong', null, label));
  }
  if (kind === 'Icon') {
    return React.createElement('span', {className: 'rsp3-icon', 'aria-label': props['aria-label'] || 'Icon'}, '●');
  }
  if (kind === 'LabeledValue') {
    return React.createElement('dl', {className: 'rsp3-labeled-value'}, React.createElement('dt', null, label), React.createElement('dd', null, props.value || 'Spectrum value'));
  }
  if (kind === 'Well') {
    return React.createElement('div', {className: 'rsp3-well'}, label);
  }
  if (kind === 'Flex' || kind === 'Grid') {
    return React.createElement('div', {className: kind === 'Grid' ? 'rsp3-grid' : 'rsp3-flex'}, React.createElement('span', null, 'A'), React.createElement('span', null, 'B'), React.createElement('span', null, 'C'));
  }
  if (['Content', 'Footer', 'Header', 'Provider', 'SSRProvider', 'View', 'VisuallyHidden'].includes(kind)) {
    return React.createElement(kind === 'Footer' ? 'footer' : kind === 'Header' ? 'header' : 'section', {className: 'rsp3-surface'}, label);
  }
  if (collectionKinds.has(kind)) {
    return collection(kind, props);
  }
  if (['Tabs', 'TabList', 'TabPanels'].includes(kind)) {
    return React.createElement('section', {className: 'rsp3-tabs'}, React.createElement('div', null, React.createElement('button', {className: 'is-selected', type: 'button'}, 'Design'), React.createElement('button', {type: 'button'}, 'Code')), React.createElement('p', null, 'Selected tab content'));
  }
  if (['Disclosure', 'DisclosurePanel', 'DisclosureTitle', 'Item', 'Section', 'Column', 'Row', 'Cell', 'TreeViewItem', 'TreeViewItemContent'].includes(kind)) {
    return React.createElement('div', {className: 'rsp3-structural'}, React.createElement('strong', null, label), React.createElement('span', null, 'Composable collection part'));
  }
  if (overlayKinds.has(kind)) {
    return overlay(kind, props);
  }

  return React.createElement('div', {className: 'rsp3-surface'}, label);
}
`;

const componentCss = `.spectrum {
  --rsp3-font-family: "Adobe Clean", "Source Sans 3", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --rsp3-font-mono: "Adobe Clean Han", "SFMono-Regular", Consolas, monospace;
  --rsp3-background: var(--spectrum-gray-50, #fff);
  --rsp3-layer: var(--spectrum-gray-75, #fdfdfd);
  --rsp3-layer-raised: var(--spectrum-gray-100, #f8f8f8);
  --rsp3-border: var(--spectrum-gray-300, #d5d5d5);
  --rsp3-border-strong: var(--spectrum-gray-500, #909090);
  --rsp3-text: var(--spectrum-gray-800, #222);
  --rsp3-text-muted: var(--spectrum-gray-600, #6d6d6d);
  --rsp3-accent: var(--spectrum-blue-900, #0265dc);
  --rsp3-accent-hover: var(--spectrum-blue-1000, #0054b6);
  --rsp3-negative: var(--spectrum-red-900, #d31510);
  --rsp3-positive: var(--spectrum-green-900, #007a4d);
  --rsp3-notice: var(--spectrum-orange-900, #b14c00);
  --rsp3-focus: var(--spectrum-blue-800, #147af3);
  --rsp3-radius-control: 4px;
  --rsp3-radius-surface: 6px;
  --rsp3-control-height: 32px;
  color: var(--rsp3-text);
  font-family: var(--rsp3-font-family);
  font-size: 14px;
  line-height: 1.5;
}

.rsp3-gallery { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; padding: 24px; background: var(--rsp3-background); }
.rsp3-gallery-item { min-width: 0; min-height: 132px; display: flex; flex-direction: column; gap: 16px; align-items: flex-start; justify-content: center; padding: 16px; border: 1px solid var(--rsp3-border); border-radius: var(--rsp3-radius-surface); background: var(--rsp3-layer); }
.rsp3-gallery-item > small { color: var(--rsp3-text-muted); font-size: 11px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
.rsp3-button { min-height: var(--rsp3-control-height); display: inline-flex; align-items: center; justify-content: center; padding: 0 14px; border: 2px solid transparent; border-radius: 16px; font: 600 14px/1 var(--rsp3-font-family); cursor: pointer; transition: background-color 130ms cubic-bezier(.45,0,.4,1), border-color 130ms cubic-bezier(.45,0,.4,1); }
.rsp3-button:focus-visible, .rsp3-field input:focus-visible, .rsp3-field textarea:focus-visible { outline: 2px solid var(--rsp3-focus); outline-offset: 2px; }
.rsp3-button-accent { color: #fff; background: var(--rsp3-accent); }
.rsp3-button-accent:hover { background: var(--rsp3-accent-hover); }
.rsp3-button-primary { color: #fff; background: var(--rsp3-text); }
.rsp3-button-secondary { color: var(--rsp3-text); border-color: var(--rsp3-border-strong); background: transparent; }
.rsp3-button-negative { color: #fff; background: var(--rsp3-negative); }
.rsp3-button-quiet { color: var(--rsp3-text); background: transparent; }
.rsp3-button:disabled { cursor: not-allowed; opacity: .42; }
.rsp3-inline-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.rsp3-field { width: min(100%, 260px); display: flex; flex-direction: column; gap: 5px; color: var(--rsp3-text-muted); font-size: 12px; font-weight: 600; }
.rsp3-field-shell { display: flex; }
.rsp3-field input, .rsp3-field textarea, .rsp3-field-shell input { box-sizing: border-box; width: 100%; min-height: var(--rsp3-control-height); padding: 5px 9px; border: 1px solid var(--rsp3-border-strong); border-radius: var(--rsp3-radius-control); color: var(--rsp3-text); background: var(--rsp3-background); font: 400 14px/1.4 var(--rsp3-font-family); }
.rsp3-field textarea { min-height: 72px; resize: vertical; }
.rsp3-field-shell input { border-radius: 4px 0 0 4px; }
.rsp3-field-shell button { width: 34px; border: 1px solid var(--rsp3-border-strong); border-left: 0; border-radius: 0 4px 4px 0; color: var(--rsp3-text); background: var(--rsp3-layer-raised); }
.rsp3-choice, .rsp3-choice-group { display: flex; gap: 8px; align-items: center; color: var(--rsp3-text); font-size: 14px; }
.rsp3-choice input { position: absolute; opacity: 0; }
.rsp3-choice > span { width: 14px; height: 14px; box-sizing: border-box; display: inline-grid; place-items: center; border: 2px solid var(--rsp3-border-strong); border-radius: 3px; }
.rsp3-choice-radio > span, .rsp3-choice-group input[type="radio"] + span { border-radius: 50%; }
.rsp3-choice input:checked + span { border-color: var(--rsp3-accent); background: var(--rsp3-accent); box-shadow: inset 0 0 0 3px var(--rsp3-background); }
.rsp3-choice-switch > span { width: 28px; border-radius: 8px; }
.rsp3-choice b { font-weight: 400; }
.rsp3-choice-group { flex-direction: column; align-items: flex-start; padding: 0; border: 0; }
.rsp3-choice-group legend { margin-bottom: 6px; color: var(--rsp3-text-muted); font-size: 12px; font-weight: 600; }
.rsp3-form { display: flex; flex-direction: column; gap: 12px; align-items: flex-start; }
.rsp3-dropzone { width: min(100%, 280px); min-height: 94px; box-sizing: border-box; display: flex; flex-direction: column; gap: 4px; align-items: center; justify-content: center; border: 2px dashed var(--rsp3-border-strong); border-radius: var(--rsp3-radius-surface); background: var(--rsp3-layer-raised); }
.rsp3-dropzone span { color: var(--rsp3-text-muted); font-size: 12px; }
.rsp3-slider { width: min(100%, 260px); display: flex; flex-direction: column; gap: 8px; color: var(--rsp3-text-muted); font-size: 12px; font-weight: 600; }
.rsp3-slider input { width: 100%; accent-color: var(--rsp3-accent); }
.rsp3-calendar { width: 260px; padding: 14px; border: 1px solid var(--rsp3-border); border-radius: var(--rsp3-radius-surface); background: var(--rsp3-background); box-shadow: 0 4px 16px rgb(0 0 0 / .12); }
.rsp3-calendar header { display: flex; gap: 8px; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.rsp3-calendar header button { border: 0; color: var(--rsp3-text); background: transparent; font-size: 20px; }
.rsp3-calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
.rsp3-calendar-grid span { width: 28px; height: 28px; display: grid; place-items: center; border-radius: 50%; font-size: 12px; }
.rsp3-calendar-grid .is-weekday { color: var(--rsp3-text-muted); font-weight: 700; }
.rsp3-calendar-grid .is-selected { color: #fff; background: var(--rsp3-accent); }
.rsp3-color-control { width: 220px; display: flex; flex-direction: column; gap: 8px; }
.rsp3-color-control > div { height: 72px; border-radius: var(--rsp3-radius-control); background: linear-gradient(90deg, #fff, #0265dc), linear-gradient(#0000, #000); box-shadow: inset 0 0 0 1px rgb(0 0 0 / .18); }
.rsp3-color-colorwheel > div { width: 88px; height: 88px; border-radius: 50%; background: conic-gradient(red, #ff0, #0f0, #0ff, #00f, #f0f, red); }
.rsp3-color-control code { color: var(--rsp3-text-muted); font-family: var(--rsp3-font-mono); }
.rsp3-color-swatch, .rsp3-swatches button { width: 34px; height: 34px; border: 3px solid var(--rsp3-background); border-radius: 4px; background: var(--rsp3-accent); box-shadow: 0 0 0 1px var(--rsp3-border-strong); }
.rsp3-swatches { display: flex; gap: 10px; }
.rsp3-swatches button { cursor: pointer; }
.rsp3-progress { width: min(100%, 260px); display: flex; flex-direction: column; gap: 7px; color: var(--rsp3-text-muted); font-size: 12px; }
.rsp3-progress progress { width: 100%; height: 7px; accent-color: var(--rsp3-accent); }
.rsp3-progress-circle { width: 58px; height: 58px; display: grid; place-items: center; border-radius: 50%; background: conic-gradient(var(--rsp3-accent) 64%, var(--rsp3-border) 0); }
.rsp3-progress-circle span { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 50%; background: var(--rsp3-background); font-size: 12px; }
.rsp3-status { display: inline-flex; gap: 8px; align-items: center; }
.rsp3-status i { width: 8px; height: 8px; border-radius: 50%; background: var(--rsp3-positive); }
.rsp3-badge { display: inline-flex; padding: 2px 8px; border-radius: 10px; color: var(--rsp3-text); background: var(--rsp3-layer-raised); font-size: 12px; font-weight: 700; }
.rsp3-avatar { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 50%; color: #fff; background: var(--rsp3-accent); font-weight: 700; }
.rsp3-divider { width: 100%; border: 0; border-top: 1px solid var(--rsp3-border); }
.rsp3-heading, .rsp3-text { margin: 0; color: var(--rsp3-text); }
.rsp3-heading { font-size: 18px; line-height: 1.3; }
.rsp3-keyboard { padding: 2px 7px; border: 1px solid var(--rsp3-border); border-bottom-width: 2px; border-radius: 4px; background: var(--rsp3-layer-raised); font-family: var(--rsp3-font-mono); }
.rsp3-link { color: var(--rsp3-accent); text-decoration: none; }
.rsp3-link:hover { text-decoration: underline; }
.rsp3-media { display: flex; gap: 10px; align-items: center; }
.rsp3-media-shape { width: 54px; height: 42px; display: grid; place-items: center; border-radius: 4px; color: var(--rsp3-text-muted); background: var(--rsp3-layer-raised); font-size: 11px; }
.rsp3-icon { width: 24px; height: 24px; display: grid; place-items: center; color: var(--rsp3-accent); }
.rsp3-labeled-value { margin: 0; }
.rsp3-labeled-value dt { color: var(--rsp3-text-muted); font-size: 12px; }
.rsp3-labeled-value dd { margin: 2px 0 0; font-weight: 600; }
.rsp3-well, .rsp3-surface { min-width: 160px; padding: 14px; border: 1px solid var(--rsp3-border); border-radius: var(--rsp3-radius-surface); background: var(--rsp3-layer-raised); }
.rsp3-flex, .rsp3-grid { display: flex; gap: 8px; }
.rsp3-grid { display: grid; grid-template-columns: repeat(3, 44px); }
.rsp3-flex span, .rsp3-grid span { min-height: 38px; display: grid; place-items: center; border-radius: 4px; background: var(--rsp3-layer-raised); }
.rsp3-collection { min-width: 220px; overflow: hidden; border: 1px solid var(--rsp3-border); border-radius: 4px; background: var(--rsp3-background); }
.rsp3-collection > * { display: block; padding: 7px 10px; }
.rsp3-collection > strong { border-bottom: 1px solid var(--rsp3-border); font-size: 12px; }
.rsp3-collection .is-selected { color: #fff; background: var(--rsp3-accent); }
.rsp3-breadcrumbs { display: flex; gap: 7px; align-items: center; }
.rsp3-breadcrumbs a { color: var(--rsp3-accent); text-decoration: none; }
.rsp3-accordion { min-width: 220px; border-top: 1px solid var(--rsp3-border); border-bottom: 1px solid var(--rsp3-border); }
.rsp3-accordion > div { padding: 8px 0; font-weight: 700; }
.rsp3-accordion p { margin: 0; padding: 0 18px 10px; color: var(--rsp3-text-muted); }
.rsp3-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.rsp3-table th, .rsp3-table td { padding: 7px 9px; border-bottom: 1px solid var(--rsp3-border); text-align: left; }
.rsp3-table th { color: var(--rsp3-text-muted); background: var(--rsp3-layer-raised); }
.rsp3-tabs { min-width: 220px; }
.rsp3-tabs > div { display: flex; gap: 16px; border-bottom: 1px solid var(--rsp3-border); }
.rsp3-tabs button { padding: 6px 0; border: 0; color: var(--rsp3-text-muted); background: transparent; }
.rsp3-tabs button.is-selected { color: var(--rsp3-accent); border-bottom: 2px solid var(--rsp3-accent); }
.rsp3-tabs p { margin: 10px 0 0; }
.rsp3-structural { display: flex; flex-direction: column; gap: 3px; padding: 9px 12px; border-left: 3px solid var(--rsp3-accent); background: var(--rsp3-layer-raised); }
.rsp3-structural span { color: var(--rsp3-text-muted); font-size: 12px; }
.rsp3-overlay { min-width: 240px; padding: 16px; border: 1px solid var(--rsp3-border); border-radius: 6px; background: var(--rsp3-background); box-shadow: 0 8px 24px rgb(0 0 0 / .16); }
.rsp3-overlay p { margin: 6px 0 14px; color: var(--rsp3-text-muted); }
@media (max-width: 720px) { .rsp3-gallery { grid-template-columns: 1fr; } }
`;

const semanticCss = `:root {
  --rsp3-source-package-version: "3.47.3";
  --rsp3-control-height-medium: 32px;
  --rsp3-control-height-large: 40px;
  --rsp3-radius-control: 4px;
  --rsp3-radius-surface: 6px;
  --rsp3-focus-width: 2px;
  --rsp3-motion-fast: 130ms;
  --rsp3-motion-standard: 160ms;
  --rsp3-motion-slow: 250ms;
}
`;

const foundationCss = `.ds-card { box-sizing: border-box; min-height: 100%; padding: 20px 24px; color: var(--rsp3-text); background: var(--rsp3-background); font-family: var(--rsp3-font-family); }
.ds-row { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; }
.ds-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }
.ds-swatch { min-height: 68px; display: flex; flex-direction: column; justify-content: flex-end; padding: 8px; border: 1px solid rgb(0 0 0 / .08); border-radius: 4px; color: #fff; font-size: 11px; font-weight: 700; }
.ds-swatch.is-light { color: #222; }
.ds-type { display: flex; flex-direction: column; gap: 4px; }
.ds-type small, .ds-note { color: var(--rsp3-text-muted); font-size: 12px; }
.ds-space { display: flex; gap: 8px; align-items: flex-end; }
.ds-space span { display: block; background: var(--rsp3-accent); }
.ds-chip { padding: 5px 9px; border: 1px solid var(--rsp3-border); border-radius: 4px; background: var(--rsp3-layer-raised); font-size: 12px; }
.ds-motion { width: 80px; height: 40px; border-radius: 20px; background: var(--rsp3-accent); animation: ds-slide 1.6s cubic-bezier(.45,0,.4,1) infinite alternate; }
.ds-illustrations { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; align-items: center; }
.ds-illustrations img { width: 100%; height: 110px; object-fit: contain; }
@keyframes ds-slide { to { transform: translateX(360px); } }
@media (prefers-reduced-motion: reduce) { .ds-motion { animation: none; } }
`;

write('styles.css', `@import "./tokens/spectrum-global.css";\n@import "./tokens/spectrum-light.css";\n@import "./tokens/spectrum-darkest.css";\n@import "./tokens/spectrum-medium.css";\n@import "./tokens/spectrum-large.css";\n@import "./tokens/semantic.css";\n@import "./components/components.css";\n@import "./guidelines/cards.css";\n`);
write('tokens/semantic.css', semanticCss);
write('components/components.css', componentCss);
write('components/shared/spectrumPrimitive.jsx', primitiveSource);
write('guidelines/cards.css', foundationCss);

for (const group of groups) {
  for (const name of group.components) {
    write(`components/${group.slug}/${name}.jsx`, componentSource(name));
    write(`components/${group.slug}/${name}.d.ts`, componentTypes(name));
    write(`components/${group.slug}/${name}.prompt.md`, componentPrompt(name, group));
  }
}

let namespace = 'ReactSpectrum3DesignSystem_pending';
const manifestPath = path.join(root, '_ds_manifest.json');
if (fs.existsSync(manifestPath)) {
  namespace = JSON.parse(fs.readFileSync(manifestPath, 'utf8')).namespace || namespace;
}

const reactScripts = `<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L" crossorigin="anonymous"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm" crossorigin="anonymous"></script>
  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y" crossorigin="anonymous"></script>`;

for (const group of groups) {
  const height = Math.max(520, Math.ceil(group.components.length / 3) * 170 + 80);
  const componentNames = JSON.stringify(group.components);
  const card = `<!-- @dsCard group="Components" viewport="960x${height}" name="${group.title}" subtitle="${group.subtitle}" -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="../../styles.css">
  <title>${group.title}</title>
</head>
<body class="spectrum spectrum--light spectrum--medium">
  <main id="root"></main>
  ${reactScripts}
  <script src="../../_ds_bundle.js"></script>
  <script type="text/babel">
    const spectrumLibrary = window.${namespace};
    const galleryNames = ${componentNames};
    function SpectrumGallery() {
      return (
        <section className="rsp3-gallery">
          {galleryNames.map((componentName) => {
            const SpectrumComponent = spectrumLibrary[componentName];
            return (
              <article className="rsp3-gallery-item" key={componentName}>
                <small>{componentName}</small>
                <SpectrumComponent label={componentName} />
              </article>
            );
          })}
        </section>
      );
    }
    ReactDOM.createRoot(document.getElementById("root")).render(<SpectrumGallery />);
  </script>
</body>
</html>
`;
  write(`components/${group.slug}/${group.slug}.card.html`, card);
}

function foundationCard(file, group, name, subtitle, height, body, bodyClass = 'spectrum spectrum--light spectrum--medium') {
  write(`guidelines/${file}.html`, `<!-- @dsCard group="${group}" viewport="700x${height}" name="${name}" subtitle="${subtitle}" -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="../styles.css">
  <title>${name}</title>
</head>
<body class="${bodyClass}">
  <main class="ds-card">${body}</main>
</body>
</html>
`);
}

foundationCard('principles', 'Principles', 'Product principles', 'Accessible, adaptive, international, and consistent.', 170, `<div class="ds-row"><span class="ds-chip">Accessible by default</span><span class="ds-chip">Mouse · touch · keyboard</span><span class="ds-chip">30+ locales</span><span class="ds-chip">Light · dark</span><span class="ds-chip">Medium · large scale</span></div><p class="ds-note">Keep labels visible, preserve focus, and let Provider own theme, locale, and scale.</p>`);
foundationCard('neutral-colors', 'Colors', 'Neutral scale', 'Surfaces, borders, and text from Spectrum gray tokens.', 180, `<div class="ds-grid"><div class="ds-swatch is-light" style="background:var(--spectrum-gray-50)">Gray 50</div><div class="ds-swatch is-light" style="background:var(--spectrum-gray-100)">Gray 100</div><div class="ds-swatch is-light" style="background:var(--spectrum-gray-200)">Gray 200</div><div class="ds-swatch" style="background:var(--spectrum-gray-500)">Gray 500</div><div class="ds-swatch" style="background:var(--spectrum-gray-700)">Gray 700</div><div class="ds-swatch" style="background:var(--spectrum-gray-900)">Gray 900</div></div>`);
foundationCard('spectrum-colors', 'Colors', 'Spectrum palette', 'Chromatic ramps use verified Spectrum source tokens.', 180, `<div class="ds-grid"><div class="ds-swatch" style="background:var(--spectrum-red-900)">Red 900</div><div class="ds-swatch" style="background:var(--spectrum-orange-900)">Orange 900</div><div class="ds-swatch" style="background:var(--spectrum-green-900)">Green 900</div><div class="ds-swatch" style="background:var(--spectrum-seafoam-900)">Seafoam 900</div><div class="ds-swatch" style="background:var(--spectrum-blue-900)">Blue 900</div><div class="ds-swatch" style="background:var(--spectrum-purple-900)">Purple 900</div></div>`);
foundationCard('semantic-colors', 'Colors', 'Semantic color', 'Accent, negative, notice, and positive roles.', 170, `<div class="ds-row"><button class="rsp3-button rsp3-button-accent">Accent</button><button class="rsp3-button rsp3-button-primary">Primary</button><button class="rsp3-button rsp3-button-negative">Negative</button><span class="rsp3-status"><i></i>Positive</span><span class="ds-chip" style="color:var(--rsp3-notice)">Notice</span></div>`);
foundationCard('themes', 'Colors', 'Theme model', 'Default light and darkest color schemes share semantic roles.', 210, `<div class="ds-row" style="align-items:stretch"><section class="spectrum spectrum--light spectrum--medium rsp3-surface" style="flex:1">Light scheme<br><small style="color:var(--rsp3-text-muted)">Gray 50 surface</small></section><section class="spectrum spectrum--darkest spectrum--medium rsp3-surface" style="flex:1">Darkest scheme<br><small style="color:var(--rsp3-text-muted)">Gray 50 surface</small></section></div>`);
foundationCard('type-hierarchy', 'Type', 'Type hierarchy', 'Adobe Clean metrics with a system-sans fallback.', 260, `<div class="ds-type"><span style="font-size:36px;font-weight:700;line-height:1.2">Display 36</span><span style="font-size:28px;font-weight:700;line-height:1.25">Heading 28</span><span style="font-size:20px;font-weight:600;line-height:1.3">Title 20</span><span style="font-size:14px;line-height:1.5">Body 14 keeps product copy compact and direct.</span></div>`);
foundationCard('type-body', 'Type', 'Body and labels', 'Sentence case, visible labels, concise supporting text.', 190, `<div class="ds-type"><strong style="font-size:14px">Project name</strong><span style="font-size:14px">Choose a clear name people can scan.</span><span class="ds-note">Optional description · 12 px</span><button class="rsp3-button rsp3-button-accent" style="align-self:flex-start">Save</button></div>`);
foundationCard('type-keyboard', 'Type', 'Keyboard and code', 'Compact monospace treatment for shortcuts and values.', 160, `<div class="ds-row"><kbd class="rsp3-keyboard">⌘ K</kbd><kbd class="rsp3-keyboard">Shift</kbd><code style="font-family:var(--rsp3-font-mono);color:var(--rsp3-accent)">#0265DC</code></div>`);
foundationCard('spacing-scale', 'Spacing', 'Spacing scale', 'Source medium-scale dimensions; no invented 4/8 grid.', 200, `<div class="ds-space"><span style="width:5px;height:20px"></span><span style="width:8px;height:32px"></span><span style="width:12px;height:48px"></span><span style="width:16px;height:64px"></span><span style="width:24px;height:96px"></span><span style="width:32px;height:128px"></span></div><p class="ds-note">5 · 8 · 12 · 16 · 24 · 32 px</p>`);
foundationCard('density', 'Spacing', 'Adaptive density', 'Medium pointer scale and larger touch scale.', 180, `<div class="ds-row"><button class="rsp3-button rsp3-button-secondary" style="min-height:32px">Medium · 32</button><button class="rsp3-button rsp3-button-secondary" style="min-height:40px;border-radius:20px">Large · 40</button><span class="ds-note">Provider selects scale by input modality.</span></div>`);
foundationCard('borders-radius', 'Spacing', 'Borders and radius', 'Quiet 1 px boundaries; 4–6 px surface radius; pill actions.', 180, `<div class="ds-row"><div class="rsp3-surface">Surface · 6 px</div><button class="rsp3-button rsp3-button-secondary">Action · pill</button><span class="rsp3-badge">Badge · pill</span></div>`);
foundationCard('motion', 'Motion', 'Motion', '130–250 ms transitions with Spectrum easing and reduced-motion support.', 170, `<div class="ds-motion"></div><p class="ds-note">cubic-bezier(.45, 0, .4, 1)</p>`);
foundationCard('iconography', 'Brand', 'Iconography', 'Spectrum UI and workflow icons; no emoji as control glyphs.', 190, `<div class="ds-row"><img src="../assets/ui-icons/SX_Info_18_N.svg" alt="Information icon" width="36" height="36"><img src="../assets/ui-icons/SX_CheckmarkCircle_18_N.svg" alt="Checkmark icon" width="36" height="36"><img src="../assets/ui-icons/SX_Alert_18_N.svg" alt="Alert icon" width="36" height="36"><span class="ds-note">Use upstream @spectrum-icons/workflow for production.</span></div>`);
foundationCard('illustrations', 'Brand', 'Component illustrations', 'Source documentation artwork copied without modification.', 220, `<div class="ds-illustrations"><img src="../assets/component-illustrations/Button.svg" alt="Button illustration"><img src="../assets/component-illustrations/Calendar.svg" alt="Calendar illustration"><img src="../assets/component-illustrations/ColorPicker.svg" alt="Color picker illustration"><img src="../assets/component-illustrations/Table.svg" alt="Table illustration"></div>`);

const inventoryMarkdown = groups.map(group => `- **${group.title}:** ${group.components.join(', ')}`).join('\n');
const sourcePath = 'C:\\haodev\\ownword\\reference\\react-spectrum-main\\react-spectrum-main';
write('readme.md', `# React Spectrum 3 Design System

React Spectrum 3 is Adobe Spectrum’s accessible React component system. This imported design source captures its public visual API, verified Spectrum tokens, component illustrations, and compact review cards for design-agent use.

## 术语与命名

- **React Spectrum 3 / RSP3：** 本目录描述的经典 Spectrum React 实现；版本来自 \`@adobe/react-spectrum@3.47.3\`。
- **Spectrum 2 / S2：** 源仓库中的新系统；本次明确排除。
- **Design component：** 面向原型的轻量视觉复刻；不是上游生产实现。
- **Provider：** 主题、色彩模式、缩放、locale 与上下文属性的根控制器。

## 目标

让后续设计只从本目录读取 React Spectrum 3 的视觉语言、token、组件名和内容规则。生产代码继续使用上游包，保留其完整可访问性、状态管理与国际化行为。

## 结构

- \`styles.css\`：唯一 CSS 入口，只含 \`@import\`。
- \`tokens/\`：上游全局、明暗模式、medium/large 缩放 token；\`semantic.css\` 只定义本导入层语义别名。
- \`components/\`：101 个公共可视导出的原型组件、props 契约、使用提示与分组预览卡。
- \`guidelines/\`：颜色、字体、间距、动效、图标、插图等基础卡。
- \`assets/\`：上游 UI SVG 与组件说明插图，保持原文件不改。
- \`tools/regenerate.mjs\`：组件清单与机械生成内容的唯一事实源。

## 实体、属性

- **Token：** 名称唯一；原始值来自上游 Spectrum CSS。明暗色与 medium/large 缩放通过 class 作用域切换。
- **Component：** PascalCase 公共名唯一；每个组件具备 \`.jsx\`、\`.d.ts\`、\`.prompt.md\`。
- **Card：** 首行 \`@dsCard\` 决定分组、名称与预览 viewport。
- **Asset：** 保留上游文件名；不从记忆重画 Adobe 标志或 Spectrum 图标。

## 关系

\`styles.css\` 导入 token 和共享组件样式；组件只消费这些变量。分组卡从 \`_ds_bundle.js\` 读取同一组件实现。\`preview.html\` 由编译器从 README、cards、manifest 生成。

## 状态

- Theme：\`spectrum--light\` 或 \`spectrum--darkest\`。
- Scale：\`spectrum--medium\` 或 \`spectrum--large\`。
- Interaction：default、hover、focus-visible、selected、disabled、negative、progress。
- Motion：0–2000 ms 上游 duration；常用原型过渡为 130–250 ms，遵守 \`prefers-reduced-motion\`。

## 界限

- 本目录是设计与原型约束，不替代 \`@adobe/react-spectrum\` 生产包。
- 不包含 Spectrum 2、React Aria 无样式组件、hooks、formatter 或 drag/drop 常量。
- 源快照未包含 Adobe Clean 字体文件。预览先请求 Adobe Clean，再回退 Source Sans 3 与系统 sans；正式品牌交付需补合法字体文件。
- 源仓库是组件库，不含可确认的产品应用界面，因此没有凭空创建 UI kit。
- 组件卡验证视觉结构；复杂键盘导航、screen reader 语义、virtualization 和 locale 逻辑仍以上游实现为准。

## Content fundamentals

使用直接、任务导向、sentence case 文案。控件保留可见标签；帮助文案解释下一步，不复述标签。按钮用短动词，如 “Save”“Cancel”“Share”。生产文案通过 \`children\` 或 \`aria-label\` 国际化。Emoji 可出现在项目说明，但不充当控制图标。

## Visual foundations

Spectrum 3 使用中性灰层级、清晰边界、蓝色 accent、状态色与小半径表面。控件在 medium scale 通常高 32 px；触摸 scale 提升到 40 px。按钮常用胶囊轮廓，字段与卡面保持 4–6 px 半径。默认阴影克制，仅 overlay 提升。背景不使用装饰渐变；渐变仅服务 ColorArea、ColorSlider、ColorWheel 等颜色工具。Hover 改变语义颜色，press 保持稳定，不用夸张缩放。Focus ring 必须可见。布局用 Flex/Grid 与显式 gap。完整数值以 \`tokens/*.css\` 为准。

## Iconography

生产组件使用 \`@spectrum-icons/ui\` 和 \`@spectrum-icons/workflow\`。本快照仅含 11 个 UI SVG 原文件，已复制到 \`assets/ui-icons/\`；workflow 图标在源中以生成式 TSX 提供，未复制成伪 SVG。组件说明插图 92 个，原样保存在 \`assets/component-illustrations/\`。未提供独立经典 Adobe 品牌 logo，因此本系统不造 logo。

## Component inventory

公共可视导出以 \`packages/@adobe/react-spectrum/exports/index.ts\` 为唯一清单，共 101 个：

${inventoryMarkdown}

## Intentional addition

\`components/shared/spectrumPrimitive.jsx\` 是导入层唯一新增 helper，用于 DRY 地生成轻量视觉预览；它不是 React Spectrum 公共 API。

## 索引与验证

- 单文件总览：\`preview.html\`
- 机器清单：\`_ds_manifest.json\`
- 运行时 bundle：\`_ds_bundle.js\`
- Adherence 规则：\`_adherence.oxlintrc.json\`
- 再生成：\`node tools/regenerate.mjs\`，随后运行 compiler、checker 与 preview builder。

## 参考文档与引用

- 本地源：\`${sourcePath}\`
- 公共导出：\`${sourcePath}\\packages\\@adobe\\react-spectrum\\exports\\index.ts\`
- 上游仓库：https://github.com/adobe/react-spectrum
- 上游文档：https://react-spectrum.adobe.com/react-spectrum/index.html
- 包版本：\`@adobe/react-spectrum@3.47.3\`
- Token 来源：\`@adobe/spectrum-css-temp\`
- 许可：Apache-2.0；见 \`LICENSE.source.txt\` 与 \`NOTICE.source.txt\`。
- 上游 Git commit 不在此解压快照中，无法可靠记录。
`);

write('SKILL.md', `---
name: react-spectrum-3-design
description: Use this skill to generate React Spectrum 3 interfaces and design artifacts with its verified tokens, public component inventory, content rules, and source assets.
user-invocable: true
---

Read \`readme.md\` first. Treat it, \`styles.css\`, and \`tokens/\` as binding visual constraints.

For visual artifacts, copy only needed assets and build static HTML from the listed tokens and components. For production code, use \`@adobe/react-spectrum\`; the local JSX files are cosmetic prototype recreations, not production accessibility implementations.

If invoked without a concrete artifact request, ask what interface or asset to create, its target viewport, and whether light/dark or medium/large scale matters.
`);

function annotateUnclassifiedTokens() {
  const tokenFiles = [
    'tokens/spectrum-global.css',
    'tokens/spectrum-light.css',
    'tokens/spectrum-darkest.css',
    'tokens/spectrum-medium.css',
    'tokens/spectrum-large.css',
    'tokens/semantic.css',
    'components/components.css',
    'guidelines/cards.css'
  ].filter(relativePath => fs.existsSync(path.join(root, relativePath)));
  const declarationPattern = /(--[A-Za-z0-9-]+)\s*:\s*([^;]+);[ \t]*(?:\/\*\s*@kind\s+([A-Za-z]+)\s*\*\/)?/g;
  const values = new Map();
  for (const relativePath of tokenFiles) {
    const css = fs.readFileSync(path.join(root, relativePath), 'utf8');
    for (const match of css.matchAll(declarationPattern)) {
      if (!match[2].includes('{') && !match[2].includes('}')) {
        values.set(match[1], match[2].trim());
      }
    }
  }
  function resolve(value, depth = 0) {
    if (depth > 10) return value;
    const match = /^var\(\s*(--[A-Za-z0-9-]+)\s*(?:,\s*([^)]+))?\)$/.exec(String(value).trim());
    if (!match) return value;
    if (values.has(match[1])) return resolve(values.get(match[1]), depth + 1);
    return match[2] ? resolve(match[2].trim(), depth + 1) : value;
  }
  function isClassified(value) {
    const resolved = String(resolve(value)).trim();
    const hasColor = /#[0-9a-fA-F]{3,8}\b/.test(resolved) || /\b(rgba?|hsla?|okl?ch|oklab|lab|lch|hwb|color)\(/.test(resolved) || ['transparent', 'currentcolor', 'black', 'white', 'red', 'green', 'blue', 'gray', 'grey'].includes(resolved.toLowerCase());
    const hasLength = /(^|[\s,(])-?\d*\.?\d+(px|rem|em|vh|vw|vmin|vmax|%|pt)\b/.test(resolved);
    return hasColor || hasLength;
  }
  for (const relativePath of tokenFiles) {
    const absolutePath = path.join(root, relativePath);
    const css = fs.readFileSync(absolutePath, 'utf8');
    const annotated = css.replace(declarationPattern, (full, name, value, annotation) => {
      if (annotation || isClassified(value)) return full;
      const kind = name.toLowerCase().includes('font') ? 'font' : 'other';
      return `${name}: ${value.trim()}; /* @kind ${kind} */`;
    });
    fs.writeFileSync(absolutePath, annotated, 'utf8');
  }
}

annotateUnclassifiedTokens();

console.log(`Generated React Spectrum 3 authoring sources: ${allComponents.length} components, ${groups.length} component cards, 14 foundation cards. Namespace: ${namespace}`);
