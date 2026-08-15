import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const upstreamRoot = 'C:\\haodev\\ownword\\reference\\react-spectrum-main\\react-spectrum-main';
const tokenSource = path.join(root, 'sources', 'spectrum-tokens-14.15.0.variables.json');

const groups = [
  {
    slug: 'actions',
    title: 'Actions',
    subtitle: 'Pill buttons, grouped actions, and interaction triggers.',
    components: ['ActionBar', 'ActionButton', 'ActionButtonGroup', 'ActionMenu', 'Button', 'ButtonGroup', 'CloseButton', 'DialogTrigger', 'DragPreview', 'FileTrigger', 'LinkButton', 'MenuTrigger', 'SubmenuTrigger', 'ToggleButton', 'ToggleButtonGroup', 'TooltipTrigger', 'UnavailableMenuItemTrigger']
  },
  {
    slug: 'forms',
    title: 'Forms and selection',
    subtitle: 'Adaptive fields, selection controls, sliders, and drop targets.',
    components: ['Autocomplete', 'Checkbox', 'CheckboxGroup', 'ComboBox', 'ComboBoxItem', 'ComboBoxSection', 'DropZone', 'Form', 'NumberField', 'Picker', 'PickerItem', 'PickerSection', 'Radio', 'RadioGroup', 'RangeSlider', 'SearchField', 'SelectBox', 'SelectBoxGroup', 'Slider', 'Switch', 'TextArea', 'TextField']
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
    subtitle: 'Color sampling, entry, and spatial controls.',
    components: ['ColorArea', 'ColorField', 'ColorSlider', 'ColorSwatch', 'ColorSwatchPicker', 'ColorWheel']
  },
  {
    slug: 'content-media',
    title: 'Content and media',
    subtitle: 'Typography, status, media, skeletons, and provider primitives.',
    components: ['Avatar', 'AvatarGroup', 'Badge', 'CenterBaseline', 'Content', 'Divider', 'Footer', 'Header', 'Heading', 'IllustratedMessage', 'Image', 'ImageCoordinator', 'Keyboard', 'LabeledValue', 'Link', 'NotificationBadge', 'Provider', 'Skeleton', 'SkeletonCollection', 'StatusLight', 'Text']
  },
  {
    slug: 'cards',
    title: 'Cards',
    subtitle: 'Primary, product, asset, user, and collection card families.',
    components: ['AssetCard', 'Card', 'CardPreview', 'CardView', 'CollectionCardPreview', 'ProductCard', 'UserCard']
  },
  {
    slug: 'collections',
    title: 'Collections and data',
    subtitle: 'Lists, tables, trees, rows, cells, and collection composition.',
    components: ['Cell', 'Collection', 'Column', 'EditableCell', 'ListView', 'ListViewItem', 'Row', 'TableBody', 'TableFooter', 'TableHeader', 'TableView', 'TreeView', 'TreeViewItem', 'TreeViewItemContent', 'TreeViewLoadMoreItem']
  },
  {
    slug: 'navigation',
    title: 'Navigation and disclosure',
    subtitle: 'Accordions, breadcrumbs, side navigation, tabs, tags, and segments.',
    components: ['Accordion', 'AccordionItem', 'AccordionItemHeader', 'AccordionItemPanel', 'AccordionItemTitle', 'Breadcrumb', 'Breadcrumbs', 'Disclosure', 'DisclosureHeader', 'DisclosurePanel', 'DisclosureTitle', 'SegmentedControl', 'SegmentedControlItem', 'SideNav', 'SideNavHeader', 'SideNavItem', 'SideNavItemContent', 'SideNavItemLink', 'SideNavSection', 'Tab', 'TabList', 'TabPanel', 'Tabs', 'Tag', 'TagGroup']
  },
  {
    slug: 'feedback-overlays',
    title: 'Feedback and overlays',
    subtitle: 'Dialogs, alerts, menus, progress, popovers, toasts, and tooltips.',
    components: ['AlertDialog', 'ContextualHelp', 'ContextualHelpPopover', 'CustomDialog', 'Dialog', 'DialogContainer', 'FullscreenDialog', 'InlineAlert', 'Menu', 'MenuItem', 'MenuSection', 'Meter', 'Popover', 'ProgressBar', 'ProgressCircle', 'ToastContainer', 'ToastQueue', 'Tooltip']
  }
];

const allComponents = groups.flatMap(group => group.components);
const uniqueComponents = new Set(allComponents);
if (allComponents.length !== 137 || uniqueComponents.size !== allComponents.length) {
  throw new Error(`Expected 137 unique S2 public visual exports, found ${allComponents.length}/${uniqueComponents.size}.`);
}

function write(relativePath, content) {
  const output = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(output), {recursive: true});
  fs.writeFileSync(output, content.replace(/\r\n/g, '\n'), 'utf8');
}

function humanize(value) {
  return value.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
}

function parseUpstreamVisualExports() {
  const indexPath = path.join(upstreamRoot, 'packages', '@react-spectrum', 's2', 'exports', 'index.ts');
  if (!fs.existsSync(indexPath)) return null;
  const source = fs.readFileSync(indexPath, 'utf8').split('export type')[0];
  const names = new Set();
  for (const block of source.matchAll(/export\s*\{([\s\S]*?)\}\s*from/g)) {
    for (const part of block[1].split(',')) {
      const name = part.trim().split(/\s+as\s+/).at(-1)?.trim();
      if (/^[A-Z][A-Za-z0-9]*$/.test(name || '') && !name.endsWith('Context')) names.add(name);
    }
  }
  return [...names].sort();
}

const upstreamComponents = parseUpstreamVisualExports();
if (upstreamComponents) {
  const localComponents = [...uniqueComponents].sort();
  const missing = upstreamComponents.filter(name => !uniqueComponents.has(name));
  const invented = localComponents.filter(name => !upstreamComponents.includes(name));
  if (missing.length || invented.length) {
    throw new Error(`S2 inventory drift. Missing: ${missing.join(', ') || 'none'}; extra: ${invented.join(', ') || 'none'}.`);
  }
}

function primitiveValue(value) {
  if (typeof value === 'string' || typeof value === 'number') return String(value);
  return null;
}

function resolveNode(node, scheme = 'light', scale = 'desktop') {
  const primitive = primitiveValue(node);
  if (primitive !== null) return primitive;
  if (!node || typeof node !== 'object') return null;
  if (Object.hasOwn(node, 'value')) return serializeValue(node.value, scheme, scale);
  if (node.sets) {
    if (node.sets[scheme]) return resolveNode(node.sets[scheme], scheme, scale);
    if (node.sets[scale]) return resolveNode(node.sets[scale], scheme, scale);
  }
  return null;
}

function serializeValue(value, scheme = 'light', scale = 'desktop') {
  const primitive = primitiveValue(value);
  if (primitive !== null) return primitive;
  if (Array.isArray(value)) {
    return value.map(layer => {
      if (!layer || typeof layer !== 'object') return String(layer);
      const color = resolveNode(layer.color, scheme, scale) || 'transparent';
      return `${layer.x || 0} ${layer.y || 0} ${layer.blur || 0} ${layer.spread || 0} ${color}`;
    }).join(', ');
  }
  if (value && typeof value === 'object' && value.fontFamily) {
    const family = resolveNode(value.fontFamily, scheme, scale) || 'sans-serif';
    const size = resolveNode(value.fontSize, scheme, scale) || '14px';
    const lineHeight = resolveNode(value.lineHeight, scheme, scale) || 'normal';
    const weight = resolveNode(value.fontWeight, scheme, scale) || 'normal';
    return `${weight} ${size}/${lineHeight} "${family}"`;
  }
  return null;
}

function tokenCss() {
  const tokens = JSON.parse(fs.readFileSync(tokenSource, 'utf8'));
  const base = [];
  const mobile = [];
  const unresolved = [];
  for (const name of Object.keys(tokens).sort()) {
    const token = tokens[name];
    let value;
    if (token.sets?.light && token.sets?.dark) {
      const light = resolveNode(token.sets.light, 'light', 'desktop');
      const dark = resolveNode(token.sets.dark, 'dark', 'desktop');
      value = light && dark && light !== dark ? `light-dark(${light}, ${dark})` : light || dark;
    } else if (token.sets?.desktop && token.sets?.mobile) {
      value = resolveNode(token.sets.desktop, 'light', 'desktop');
      const touchValue = resolveNode(token.sets.mobile, 'light', 'mobile');
      if (touchValue && touchValue !== value) mobile.push(`    --s2-${name}: ${touchValue};`);
    } else {
      value = resolveNode(token, 'light', 'desktop');
    }
    if (!value) {
      unresolved.push(name);
      value = 'initial';
    }
    base.push(`  --s2-${name}: ${value};`);
  }
  if (unresolved.length) throw new Error(`Unresolved S2 tokens: ${unresolved.join(', ')}`);
  return `:root {\n${base.join('\n')}\n}\n\n@media not ((hover: hover) and (pointer: fine)) {\n  :root {\n${mobile.join('\n')}\n  }\n}\n`;
}

function componentSource(name) {
  return `import {renderS2Component} from '../shared/s2Primitive.jsx';\n\nexport function ${name}(props) {\n  return renderS2Component('${name}', props);\n}\n`;
}

function componentTypes(name) {
  return `import type {ReactElement, ReactNode} from 'react';\n\nexport interface ${name}Props {\n  children?: ReactNode;\n  label?: string;\n  description?: string;\n  value?: string | number;\n  variant?: 'accent' | 'primary' | 'secondary' | 'negative' | 'premium' | 'genai' | 'neutral' | 'quiet';\n  fillStyle?: 'fill' | 'outline';\n  size?: 'XS' | 'S' | 'M' | 'L' | 'XL';\n  isDisabled?: boolean;\n  isSelected?: boolean;\n  isQuiet?: boolean;\n  isEmphasized?: boolean;\n  onPress?: () => void;\n  className?: string;\n  'aria-label'?: string;\n}\n\nexport declare function ${name}(props: ${name}Props): ReactElement;\n`;
}

function componentPrompt(name, group) {
  return `${name} recreates the Spectrum 2 ${humanize(name).toLowerCase()} visual family for ${group.title.toLowerCase()} prototypes.\n\n\`\`\`jsx\n<${name} label="${humanize(name)}" />\n\`\`\`\n\nUse S2 adaptive sizing, visible focus, light/dark color roles, and sentence-case labels. This local component is cosmetic; production behavior and accessibility belong to \`@react-spectrum/s2\`.\n`;
}

const primitiveSource = `import React from 'react';

const buttonKinds = new Set(['ActionButton', 'ActionMenu', 'Button', 'CloseButton', 'DialogTrigger', 'FileTrigger', 'LinkButton', 'MenuTrigger', 'SubmenuTrigger', 'ToggleButton', 'TooltipTrigger', 'UnavailableMenuItemTrigger']);
const fieldKinds = new Set(['Autocomplete', 'ColorField', 'ComboBox', 'DateField', 'DatePicker', 'DateRangePicker', 'NumberField', 'Picker', 'SearchField', 'TextField', 'TimeField']);
const calendarKinds = new Set(['Calendar', 'RangeCalendar']);
const cardKinds = new Set(['AssetCard', 'Card', 'CardPreview', 'CollectionCardPreview', 'ProductCard', 'UserCard']);
const collectionKinds = new Set(['Collection', 'ListView', 'TableView', 'TreeView']);
const overlayKinds = new Set(['AlertDialog', 'ContextualHelp', 'ContextualHelpPopover', 'CustomDialog', 'Dialog', 'DialogContainer', 'FullscreenDialog', 'InlineAlert', 'Popover', 'ToastContainer', 'ToastQueue', 'Tooltip']);

function labelFor(kind, props) {
  return props.children || props.label || kind.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
}

function calendar(kind, props) {
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S', '29', '30', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
  return React.createElement('section', {className: 's2d-calendar', 'aria-label': props['aria-label'] || kind},
    React.createElement('header', null, React.createElement('button', {type: 'button'}, 'Prev'), React.createElement('strong', null, kind === 'RangeCalendar' ? 'April – May 2026' : 'April 2026'), React.createElement('button', {type: 'button'}, 'Next')),
    React.createElement('div', {className: 's2d-calendar-grid'}, days.map((day, index) => React.createElement('span', {className: index === 12 ? 'is-selected' : index < 7 ? 'is-weekday' : '', key: index}, day)))
  );
}

function card(kind, props) {
  return React.createElement('article', {className: 's2d-card'},
    React.createElement('div', {className: 's2d-card-preview'}, kind.includes('User') ? 'U' : kind.includes('Product') ? 'P' : 'S2'),
    React.createElement('strong', null, labelFor(kind, props)),
    React.createElement('span', null, props.description || 'Adaptive Spectrum 2 content'));
}

function collection(kind, props) {
  const label = labelFor(kind, props);
  if (kind === 'TableView') {
    return React.createElement('table', {className: 's2d-table'}, React.createElement('thead', null, React.createElement('tr', null, React.createElement('th', null, 'Name'), React.createElement('th', null, 'Status'))), React.createElement('tbody', null, React.createElement('tr', null, React.createElement('td', null, 'Concept.fig'), React.createElement('td', null, 'Ready')), React.createElement('tr', null, React.createElement('td', null, 'Review.pdf'), React.createElement('td', null, 'Shared'))));
  }
  return React.createElement('section', {className: 's2d-collection'}, React.createElement('strong', null, label), React.createElement('div', {className: 'is-selected'}, 'Selected item'), React.createElement('div', null, 'Second item'), React.createElement('div', null, 'Third item'));
}

function overlay(kind, props) {
  return React.createElement('section', {className: 's2d-overlay'}, React.createElement('strong', null, labelFor(kind, props)), React.createElement('p', null, props.description || 'A concise message with a clear next action.'), React.createElement('div', {className: 's2d-inline-actions'}, React.createElement('button', {className: 's2d-button s2d-button-secondary', type: 'button'}, 'Cancel'), React.createElement('button', {className: 's2d-button s2d-button-accent', type: 'button'}, 'Confirm')));
}

export function renderS2Component(kind, props = {}) {
  const label = labelFor(kind, props);
  const disabled = Boolean(props.isDisabled);
  if (buttonKinds.has(kind)) {
    const variant = props.variant || (kind === 'Button' || kind === 'LinkButton' ? 'accent' : 'secondary');
    const Element = kind === 'LinkButton' ? 'a' : 'button';
    return React.createElement(Element, {className: \`s2d-button s2d-button-\${variant}\`, disabled, href: Element === 'a' ? '#' : undefined, onClick: props.onPress, type: Element === 'button' ? 'button' : undefined}, label);
  }
  if (['ActionBar', 'ActionButtonGroup', 'ButtonGroup', 'ToggleButtonGroup'].includes(kind)) {
    return React.createElement('div', {className: 's2d-inline-actions'}, React.createElement('button', {className: 's2d-button s2d-button-secondary', type: 'button'}, 'Edit'), React.createElement('button', {className: 's2d-button s2d-button-secondary', type: 'button'}, 'Share'), React.createElement('button', {className: 's2d-button s2d-button-quiet', type: 'button'}, 'More'));
  }
  if (['Checkbox', 'Radio', 'Switch'].includes(kind)) {
    const inputType = kind === 'Radio' ? 'radio' : 'checkbox';
    return React.createElement('label', {className: \`s2d-choice s2d-choice-\${kind.toLowerCase()}\`}, React.createElement('input', {type: inputType, defaultChecked: props.isSelected !== false, disabled}), React.createElement('span', null), React.createElement('b', null, label));
  }
  if (kind === 'CheckboxGroup' || kind === 'RadioGroup') {
    const inputType = kind === 'RadioGroup' ? 'radio' : 'checkbox';
    return React.createElement('fieldset', {className: 's2d-choice-group'}, React.createElement('legend', null, label), ['First option', 'Second option'].map((item, index) => React.createElement('label', {className: 's2d-choice', key: item}, React.createElement('input', {type: inputType, name: kind, defaultChecked: index === 0}), React.createElement('span', null), React.createElement('b', null, item))));
  }
  if (fieldKinds.has(kind)) {
    const fieldType = kind === 'SearchField' ? 'search' : kind === 'NumberField' ? 'number' : 'text';
    return React.createElement('label', {className: 's2d-field'}, React.createElement('span', null, label), React.createElement('div', {className: 's2d-field-shell'}, React.createElement('input', {type: fieldType, defaultValue: props.value || (kind.includes('Date') ? 'Apr 15, 2026' : 'Spectrum 2 value'), disabled}), React.createElement('button', {type: 'button', tabIndex: -1}, kind === 'SearchField' ? 'Clear' : 'Open')));
  }
  if (kind === 'TextArea') return React.createElement('label', {className: 's2d-field'}, React.createElement('span', null, label), React.createElement('textarea', {defaultValue: props.value || 'Write a clear description.', disabled}));
  if (kind === 'Form') return React.createElement('form', {className: 's2d-form'}, React.createElement('label', {className: 's2d-field'}, React.createElement('span', null, 'Project name'), React.createElement('input', {defaultValue: 'Spectrum 2 project'})), React.createElement('button', {className: 's2d-button s2d-button-accent', type: 'button'}, 'Save'));
  if (kind === 'DropZone') return React.createElement('div', {className: 's2d-dropzone'}, React.createElement('strong', null, 'Drop files here'), React.createElement('span', null, 'or choose from your computer'));
  if (kind === 'Slider' || kind === 'RangeSlider') return React.createElement('label', {className: 's2d-slider'}, React.createElement('span', null, label), React.createElement('input', {type: 'range', min: 0, max: 100, defaultValue: kind === 'RangeSlider' ? 68 : 42}));
  if (calendarKinds.has(kind)) return calendar(kind, props);
  if (kind.startsWith('Color')) {
    if (kind === 'ColorSwatch') return React.createElement('div', {className: 's2d-color-swatch', title: 'rgb(59, 99, 251)'});
    if (kind === 'ColorSwatchPicker') return React.createElement('div', {className: 's2d-swatches'}, ['#3b63fb', '#e34850', '#2d9d78', '#f0a30a', '#9b55d9'].map(color => React.createElement('button', {key: color, style: {background: color}, title: color, type: 'button'})));
    return React.createElement('section', {className: \`s2d-color-control s2d-color-\${kind.toLowerCase()}\`}, React.createElement('div', null), React.createElement('code', null, 'rgb(59, 99, 251)'));
  }
  if (kind === 'ProgressBar' || kind === 'Meter') return React.createElement('label', {className: 's2d-progress'}, React.createElement('span', null, label, ' · 68%'), React.createElement('progress', {max: 100, value: 68}));
  if (kind === 'ProgressCircle') return React.createElement('div', {className: 's2d-progress-circle'}, React.createElement('span', null, '68'));
  if (kind === 'StatusLight') return React.createElement('span', {className: 's2d-status'}, React.createElement('i', null), label);
  if (kind === 'Badge' || kind === 'NotificationBadge') return React.createElement('span', {className: kind === 'Badge' ? 's2d-badge' : 's2d-notification-badge'}, kind === 'NotificationBadge' ? '3' : label);
  if (kind === 'Avatar' || kind === 'AvatarGroup') return React.createElement('div', {className: 's2d-avatar-group'}, React.createElement('div', {className: 's2d-avatar'}, 'S2'), kind === 'AvatarGroup' ? React.createElement('div', {className: 's2d-avatar'}, 'UI') : null);
  if (cardKinds.has(kind)) return card(kind, props);
  if (kind === 'CardView') return React.createElement('div', {className: 's2d-card-view'}, card('Card', {label: 'First'}), card('Card', {label: 'Second'}));
  if (collectionKinds.has(kind)) return collection(kind, props);
  if (kind === 'Breadcrumbs') return React.createElement('nav', {className: 's2d-breadcrumbs'}, React.createElement('a', {href: '#'}, 'Home'), React.createElement('span', null, '/'), React.createElement('a', {href: '#'}, 'Assets'), React.createElement('span', null, '/'), React.createElement('strong', null, 'Current'));
  if (kind === 'Accordion' || kind === 'Disclosure') return React.createElement('div', {className: 's2d-disclosure'}, React.createElement('strong', null, label), React.createElement('p', null, 'Expanded Spectrum 2 content.'));
  if (['Tabs', 'TabList', 'TabPanel', 'SegmentedControl'].includes(kind)) return React.createElement('section', {className: 's2d-tabs'}, React.createElement('div', null, React.createElement('button', {className: 'is-selected', type: 'button'}, 'Design'), React.createElement('button', {type: 'button'}, 'Code')), React.createElement('p', null, 'Selected content'));
  if (kind === 'TagGroup') return React.createElement('div', {className: 's2d-tags'}, React.createElement('span', null, 'Design'), React.createElement('span', null, 'Review'), React.createElement('span', null, 'Ready'));
  if (kind === 'SideNav') return React.createElement('nav', {className: 's2d-sidenav'}, React.createElement('strong', null, label), React.createElement('a', {className: 'is-selected', href: '#'}, 'Overview'), React.createElement('a', {href: '#'}, 'Assets'));
  if (kind === 'Menu') return React.createElement('div', {className: 's2d-menu'}, React.createElement('div', null, 'Open'), React.createElement('div', {className: 'is-selected'}, 'Share'), React.createElement('div', null, 'Download'));
  if (overlayKinds.has(kind)) return overlay(kind, props);
  if (kind === 'Skeleton' || kind === 'SkeletonCollection') return React.createElement('div', {className: 's2d-skeleton'}, React.createElement('span', null), React.createElement('span', null), React.createElement('span', null));
  if (kind === 'Divider') return React.createElement('hr', {className: 's2d-divider'});
  if (kind === 'Heading') return React.createElement('h3', {className: 's2d-heading'}, label);
  if (kind === 'Text') return React.createElement('p', {className: 's2d-text'}, label);
  if (kind === 'Keyboard') return React.createElement('kbd', {className: 's2d-keyboard'}, 'Cmd K');
  if (kind === 'Link') return React.createElement('a', {className: 's2d-link', href: '#'}, label);
  if (kind === 'Image' || kind === 'IllustratedMessage') return React.createElement('div', {className: 's2d-media'}, React.createElement('div', {className: 's2d-media-shape'}, kind === 'Image' ? 'Image' : 'Message'), React.createElement('strong', null, label));
  if (kind === 'LabeledValue') return React.createElement('dl', {className: 's2d-labeled-value'}, React.createElement('dt', null, label), React.createElement('dd', null, props.value || 'Spectrum 2 value'));
  if (kind === 'Provider') return React.createElement('div', {className: 's2d-provider'}, 'Adaptive light · dark · touch');
  if (kind === 'CenterBaseline') return React.createElement('div', {className: 's2d-baseline'}, React.createElement('span', null, 'Aa'), React.createElement('span', null, '20'));
  return React.createElement('div', {className: 's2d-structural'}, React.createElement('strong', null, label), React.createElement('span', null, 'Composable S2 part'));
}
`;

const componentCss = `.s2 {
  --s2d-font-family: "adobe-clean-spectrum-vf", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --s2d-font-serif: "adobe-clean-spectrum-srf-vf", Georgia, serif;
  --s2d-font-mono: "source-code-pro", "SFMono-Regular", Consolas, monospace;
  --s2d-background: var(--s2-background-base-color, light-dark(rgb(255, 255, 255), rgb(17, 17, 17)));
  --s2d-layer: var(--s2-background-layer-1-color, light-dark(rgb(248, 248, 248), rgb(27, 27, 27)));
  --s2d-layer-raised: var(--s2-background-layer-2-color, light-dark(rgb(255, 255, 255), rgb(34, 34, 34)));
  --s2d-border: var(--s2-gray-200, light-dark(rgb(211, 211, 211), rgb(67, 67, 67)));
  --s2d-border-strong: var(--s2-gray-300, light-dark(rgb(183, 183, 183), rgb(82, 82, 82)));
  --s2d-text: var(--s2-neutral-content-color-default, light-dark(rgb(44, 44, 44), rgb(226, 226, 226)));
  --s2d-text-muted: var(--s2-neutral-subdued-content-color-default, light-dark(rgb(94, 94, 94), rgb(173, 173, 173)));
  --s2d-accent: var(--s2-accent-color-900, light-dark(rgb(59, 99, 251), rgb(86, 129, 255)));
  --s2d-accent-hover: var(--s2-accent-color-1000, light-dark(rgb(39, 77, 234), rgb(105, 149, 254)));
  --s2d-negative: var(--s2-negative-color-900, light-dark(rgb(211, 52, 62), rgb(239, 82, 91)));
  --s2d-positive: var(--s2-positive-color-900, light-dark(rgb(27, 135, 98), rgb(49, 168, 125)));
  --s2d-notice: var(--s2-notice-color-900, light-dark(rgb(183, 117, 0), rgb(231, 157, 14)));
  --s2d-focus: var(--s2-focus-ring-color, var(--s2d-accent));
  --s2d-radius-sm: 4px;
  --s2d-radius: 8px;
  --s2d-radius-lg: 10px;
  --s2d-radius-xl: 16px;
  --s2d-control-height: calc(32px * var(--s2-scale, 1));
  color: var(--s2d-text);
  background: var(--s2d-background);
  font-family: var(--s2d-font-family);
  font-size: calc(var(--s2-font-size-base, 14) * 1px);
  line-height: 1.45;
}

.s2d-gallery { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; padding: 24px; background: var(--s2d-background); }
.s2d-gallery-item { min-width: 0; min-height: 144px; display: flex; flex-direction: column; gap: 16px; align-items: flex-start; justify-content: center; padding: 18px; border: 1px solid var(--s2d-border); border-radius: var(--s2d-radius-xl); background: var(--s2d-layer-raised); box-shadow: 0 1px 2px rgb(0 0 0 / .06); }
.s2d-gallery-item > small { color: var(--s2d-text-muted); font-size: 11px; font-weight: 700; letter-spacing: .045em; text-transform: uppercase; }
.s2d-button { min-height: var(--s2d-control-height); display: inline-flex; align-items: center; justify-content: center; padding: 0 calc(var(--s2d-control-height) / 2); border: 2px solid transparent; border-radius: 999px; color: var(--s2d-text); background: transparent; font: 700 14px/1 var(--s2d-font-family); text-decoration: none; cursor: pointer; transition: color 150ms cubic-bezier(.45,0,.4,1), background 150ms cubic-bezier(.45,0,.4,1), border-color 150ms cubic-bezier(.45,0,.4,1), transform 150ms cubic-bezier(.45,0,.4,1); }
.s2d-button:hover { transform: translateY(-1px); }
.s2d-button:active { transform: translateY(0); }
.s2d-button:focus-visible, .s2d-field input:focus-visible, .s2d-field textarea:focus-visible { outline: 2px solid var(--s2d-focus); outline-offset: 2px; }
.s2d-button-accent { color: white; background: var(--s2d-accent); }
.s2d-button-accent:hover { background: var(--s2d-accent-hover); }
.s2d-button-primary { color: white; background: var(--s2d-text); }
.s2d-button-secondary { border-color: var(--s2d-border-strong); background: var(--s2d-layer); }
.s2d-button-negative { color: white; background: var(--s2d-negative); }
.s2d-button-premium { color: white; background: linear-gradient(to bottom right, var(--s2-fuchsia-900), var(--s2-indigo-900) 66%, var(--s2-blue-900)); }
.s2d-button-genai { color: white; background: linear-gradient(to bottom right, var(--s2-red-900), var(--s2-magenta-900) 33%, var(--s2-indigo-900)); }
.s2d-button-quiet { background: transparent; }
.s2d-button:disabled { cursor: not-allowed; opacity: .42; transform: none; }
.s2d-inline-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.s2d-field { width: min(100%, 280px); display: flex; flex-direction: column; gap: 6px; color: var(--s2d-text-muted); font-size: 12px; font-weight: 600; }
.s2d-field-shell { display: flex; width: 100%; }
.s2d-field input, .s2d-field textarea, .s2d-field-shell input { box-sizing: border-box; width: 100%; min-height: var(--s2d-control-height); padding: 6px 10px; border: 2px solid var(--s2d-border-strong); border-radius: var(--s2d-radius); color: var(--s2d-text); background: var(--s2-gray-25, white); font: 400 14px/1.4 var(--s2d-font-family); }
.s2d-field textarea { min-height: 78px; resize: vertical; }
.s2d-field-shell input { border-radius: var(--s2d-radius) 0 0 var(--s2d-radius); border-right: 0; }
.s2d-field-shell button { min-width: 54px; border: 2px solid var(--s2d-border-strong); border-radius: 0 var(--s2d-radius) var(--s2d-radius) 0; color: var(--s2d-text); background: var(--s2d-layer); font: 600 11px var(--s2d-font-family); }
.s2d-form { display: grid; gap: 14px; }
.s2d-choice-group { display: grid; gap: 10px; margin: 0; padding: 0; border: 0; }
.s2d-choice-group legend { margin-bottom: 8px; font-weight: 700; }
.s2d-choice { display: inline-flex; align-items: center; gap: 9px; min-height: 24px; cursor: pointer; }
.s2d-choice input { position: absolute; opacity: 0; }
.s2d-choice > span { width: 18px; height: 18px; display: grid; place-items: center; border: 2px solid var(--s2d-border-strong); border-radius: 5px; background: var(--s2-gray-25, white); }
.s2d-choice-radio > span { border-radius: 50%; }
.s2d-choice-switch > span { width: 34px; border-radius: 999px; }
.s2d-choice input:checked + span { border-color: var(--s2d-accent); background: var(--s2d-accent); box-shadow: inset 0 0 0 4px var(--s2-gray-25, white); }
.s2d-choice b { font-size: 14px; font-weight: 500; }
.s2d-dropzone { min-width: 250px; display: grid; gap: 5px; justify-items: center; padding: 24px; border: 2px dashed var(--s2d-border-strong); border-radius: var(--s2d-radius-xl); background: var(--s2d-layer); }
.s2d-dropzone span { color: var(--s2d-text-muted); font-size: 12px; }
.s2d-slider { min-width: 260px; display: grid; gap: 10px; font-weight: 600; }
.s2d-slider input { width: 100%; accent-color: var(--s2d-accent); }
.s2d-calendar { width: 276px; padding: 16px; border-radius: var(--s2d-radius-xl); background: var(--s2d-layer-raised); box-shadow: 0 4px 16px rgb(0 0 0 / .12); }
.s2d-calendar header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.s2d-calendar header button { border: 0; border-radius: 999px; padding: 5px 8px; background: var(--s2d-layer); font: 600 11px var(--s2d-font-family); }
.s2d-calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-top: 12px; }
.s2d-calendar-grid span { aspect-ratio: 1; display: grid; place-items: center; border-radius: 50%; font-size: 12px; }
.s2d-calendar-grid .is-weekday { color: var(--s2d-text-muted); font-weight: 700; }
.s2d-calendar-grid .is-selected { color: white; background: var(--s2d-accent); }
.s2d-color-control { display: flex; align-items: center; gap: 12px; }
.s2d-color-control > div { width: 160px; height: 72px; border-radius: var(--s2d-radius); background: linear-gradient(135deg, white, var(--s2d-accent) 55%, black); }
.s2d-color-swatch { width: 56px; height: 56px; border: 4px solid white; border-radius: var(--s2d-radius); background: var(--s2d-accent); box-shadow: 0 0 0 2px var(--s2d-border-strong); }
.s2d-swatches { display: flex; gap: 10px; }
.s2d-swatches button { width: 38px; height: 38px; border: 3px solid white; border-radius: var(--s2d-radius); box-shadow: 0 0 0 1px var(--s2d-border-strong); }
.s2d-progress { min-width: 260px; display: grid; gap: 8px; }
.s2d-progress progress { width: 100%; height: 8px; accent-color: var(--s2d-accent); }
.s2d-progress-circle { width: 56px; height: 56px; display: grid; place-items: center; border: 7px solid var(--s2d-border); border-top-color: var(--s2d-accent); border-radius: 50%; font-size: 11px; }
.s2d-status { display: inline-flex; align-items: center; gap: 8px; }
.s2d-status i { width: 9px; height: 9px; border-radius: 50%; background: var(--s2d-positive); }
.s2d-badge, .s2d-notification-badge { display: inline-flex; align-items: center; min-height: 22px; padding: 0 10px; border-radius: 999px; color: var(--s2d-text); background: var(--s2d-layer); font-size: 12px; font-weight: 700; }
.s2d-notification-badge { min-width: 22px; justify-content: center; padding: 0; color: white; background: var(--s2d-negative); }
.s2d-avatar-group { display: flex; }
.s2d-avatar { width: 44px; height: 44px; display: grid; place-items: center; margin-left: -6px; border: 3px solid var(--s2d-background); border-radius: 50%; color: white; background: linear-gradient(135deg, var(--s2-fuchsia-900), var(--s2-indigo-900)); font-weight: 800; }
.s2d-avatar:first-child { margin-left: 0; }
.s2d-card { width: 220px; display: grid; gap: 8px; padding: 14px; border-radius: var(--s2d-radius-lg); background: var(--s2d-layer-raised); box-shadow: 0 2px 8px rgb(0 0 0 / .10); }
.s2d-card-preview { height: 80px; display: grid; place-items: center; margin: -14px -14px 4px; border-radius: var(--s2d-radius-lg) var(--s2d-radius-lg) 0 0; color: white; background: linear-gradient(135deg, var(--s2-fuchsia-900), var(--s2-indigo-900) 60%, var(--s2-blue-900)); font: 800 20px var(--s2d-font-family); }
.s2d-card span { color: var(--s2d-text-muted); font-size: 12px; }
.s2d-card-view { display: flex; gap: 14px; }
.s2d-collection, .s2d-menu, .s2d-sidenav { min-width: 250px; display: grid; gap: 4px; padding: 8px; border-radius: var(--s2d-radius-lg); background: var(--s2d-layer); }
.s2d-collection > *, .s2d-menu > *, .s2d-sidenav > * { padding: 9px 11px; border-radius: var(--s2d-radius); }
.s2d-collection .is-selected, .s2d-menu .is-selected, .s2d-sidenav .is-selected { color: white; background: var(--s2d-accent); }
.s2d-sidenav a { color: inherit; text-decoration: none; }
.s2d-table { min-width: 300px; border-collapse: separate; border-spacing: 0; overflow: hidden; border: 1px solid var(--s2d-border); border-radius: var(--s2d-radius-lg); }
.s2d-table th, .s2d-table td { padding: 9px 12px; border-bottom: 1px solid var(--s2d-border); text-align: left; }
.s2d-table tr:last-child td { border-bottom: 0; }
.s2d-breadcrumbs { display: flex; gap: 8px; align-items: center; }
.s2d-breadcrumbs a { color: var(--s2d-accent); }
.s2d-disclosure { min-width: 280px; padding: 14px; border-radius: var(--s2d-radius-lg); background: var(--s2d-layer); }
.s2d-disclosure p { margin: 8px 0 0; color: var(--s2d-text-muted); }
.s2d-tabs { min-width: 290px; }
.s2d-tabs > div { display: flex; gap: 24px; border-bottom: 1px solid var(--s2d-border); }
.s2d-tabs button { padding: 8px 2px; border: 0; border-bottom: 3px solid transparent; color: var(--s2d-text-muted); background: transparent; font: 600 14px var(--s2d-font-family); }
.s2d-tabs button.is-selected { border-color: var(--s2d-accent); color: var(--s2d-text); }
.s2d-tabs p { color: var(--s2d-text-muted); }
.s2d-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.s2d-tags span { padding: 6px 10px; border-radius: 999px; background: var(--s2d-layer); }
.s2d-overlay { width: 310px; padding: 20px; border-radius: var(--s2d-radius-xl); background: var(--s2d-layer-raised); box-shadow: 0 12px 32px rgb(0 0 0 / .18); }
.s2d-overlay p { color: var(--s2d-text-muted); }
.s2d-skeleton { width: 260px; display: grid; gap: 10px; }
.s2d-skeleton span { height: 14px; border-radius: 999px; background: linear-gradient(90deg, var(--s2-gray-100), var(--s2-gray-25), var(--s2-gray-100)); background-size: 200% 100%; animation: s2d-shimmer 1.4s linear infinite; }
.s2d-skeleton span:nth-child(2) { width: 80%; }
.s2d-skeleton span:nth-child(3) { width: 58%; }
.s2d-divider { width: 260px; border: 0; border-top: 1px solid var(--s2d-border); }
.s2d-heading { margin: 0; font: 800 22px/1.2 var(--s2d-font-family); }
.s2d-text { margin: 0; }
.s2d-keyboard { padding: 5px 8px; border: 1px solid var(--s2d-border); border-bottom-width: 3px; border-radius: 6px; background: var(--s2d-layer); font-family: var(--s2d-font-mono); }
.s2d-link { color: var(--s2d-accent); font-weight: 600; }
.s2d-media { display: flex; gap: 12px; align-items: center; }
.s2d-media-shape { width: 80px; height: 60px; display: grid; place-items: center; border-radius: var(--s2d-radius-lg); color: white; background: linear-gradient(135deg, var(--s2-magenta-900), var(--s2-indigo-900)); }
.s2d-labeled-value { display: grid; gap: 4px; margin: 0; }
.s2d-labeled-value dt { color: var(--s2d-text-muted); font-size: 12px; }
.s2d-labeled-value dd { margin: 0; font-weight: 700; }
.s2d-provider, .s2d-structural, .s2d-baseline { display: flex; gap: 10px; align-items: center; padding: 12px 14px; border-radius: var(--s2d-radius-lg); background: var(--s2d-layer); }
.s2d-structural { flex-direction: column; align-items: flex-start; }
.s2d-structural span { color: var(--s2d-text-muted); font-size: 12px; }
.s2d-baseline span:first-child { font-size: 24px; }
@keyframes s2d-shimmer { to { background-position: -200% 0; } }
@media (prefers-reduced-motion: reduce) { .s2d-button, .s2d-skeleton span { transition: none; animation: none; } }
`;

const semanticCss = `:root {
  --s2d-font-family: "adobe-clean-spectrum-vf", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --s2d-font-serif: "adobe-clean-spectrum-srf-vf", Georgia, serif;
  --s2d-font-mono: "source-code-pro", "SFMono-Regular", Consolas, monospace;
  --s2d-surface-base: var(--s2-background-base-color);
  --s2d-surface-layer-1: var(--s2-background-layer-1-color);
  --s2d-surface-layer-2: var(--s2-background-layer-2-color);
  --s2d-content-neutral: var(--s2-neutral-content-color-default);
  --s2d-content-subdued: var(--s2-neutral-subdued-content-color-default);
  --s2d-action-accent: var(--s2-accent-color-900);
  --s2d-action-negative: var(--s2-negative-color-900);
  --s2d-status-positive: var(--s2-positive-color-900);
  --s2d-status-notice: var(--s2-notice-color-900);
  --s2d-radius-small: 4px;
  --s2d-radius-medium: 8px;
  --s2d-radius-large: 10px;
  --s2d-radius-extra-large: 16px;
  --s2d-duration-default: 150ms;
  --s2d-easing-default: cubic-bezier(0.45, 0, 0.4, 1);
}
`;

const foundationCss = `.ds-card { box-sizing: border-box; min-height: 100%; padding: 20px 24px; color: var(--s2d-text); background: var(--s2d-background); font-family: var(--s2d-font-family); }
.ds-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.ds-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }
.ds-swatch { min-height: 76px; display: flex; align-items: flex-end; padding: 8px; border-radius: var(--s2d-radius); color: white; font-size: 11px; font-weight: 700; }
.ds-swatch.is-light { color: #111; border: 1px solid var(--s2d-border); }
.ds-type { display: grid; gap: 10px; }
.ds-note { color: var(--s2d-text-muted); font-size: 12px; line-height: 1.5; }
.ds-space { display: flex; gap: 10px; align-items: flex-end; }
.ds-space span { display: block; min-width: 10px; border-radius: 3px 3px 0 0; background: var(--s2d-accent); }
.ds-chip { padding: 6px 10px; border-radius: 999px; background: var(--s2d-layer); font-size: 12px; }
.ds-layer { flex: 1; min-width: 150px; padding: 18px; border-radius: var(--s2d-radius-lg); box-shadow: 0 2px 8px rgb(0 0 0 / .10); }
.ds-motion { width: 72px; height: 40px; border-radius: 999px; background: var(--s2d-accent); animation: ds-slide 1.6s cubic-bezier(.45,0,.4,1) infinite alternate; }
.ds-icons { display: grid; grid-template-columns: repeat(8, 1fr); gap: 16px; align-items: center; }
.ds-icons img { width: 30px; height: 30px; justify-self: center; }
.ds-illustrations { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; align-items: center; }
.ds-illustrations img { width: 100%; height: 96px; object-fit: contain; }
@keyframes ds-slide { to { transform: translateX(420px); } }
@media (prefers-reduced-motion: reduce) { .ds-motion { animation: none; } }
`;

write('tokens/s2-tokens.css', tokenCss());
write('tokens/semantic.css', semanticCss);
write('components/components.css', componentCss);
write('components/shared/s2Primitive.jsx', primitiveSource);
write('guidelines/cards.css', foundationCss);
write('styles.css', `@import "./tokens/font-faces.css";\n@import "./tokens/page.css";\n@import "./tokens/s2-tokens.css";\n@import "./tokens/semantic.css";\n@import "./components/components.css";\n@import "./guidelines/cards.css";\n`);

for (const group of groups) {
  for (const name of group.components) {
    write(`components/${group.slug}/${name}.jsx`, componentSource(name));
    write(`components/${group.slug}/${name}.d.ts`, componentTypes(name));
    write(`components/${group.slug}/${name}.prompt.md`, componentPrompt(name, group));
  }
}

write('sources/public-components.json', JSON.stringify({package: '@react-spectrum/s2', version: '1.6.0', count: allComponents.length, groups}, null, 2) + '\n');

let namespace = 'ReactSpectrumS2DesignSystem_pending';
const manifestPath = path.join(root, '_ds_manifest.json');
if (fs.existsSync(manifestPath)) namespace = JSON.parse(fs.readFileSync(manifestPath, 'utf8')).namespace || namespace;

const reactScripts = `<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L" crossorigin="anonymous"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm" crossorigin="anonymous"></script>
  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y" crossorigin="anonymous"></script>`;

for (const group of groups) {
  const height = Math.max(520, Math.ceil(group.components.length / 3) * 180 + 80);
  const card = `<!-- @dsCard group="Components" viewport="960x${height}" name="${group.title}" subtitle="${group.subtitle}" -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="../../styles.css">
  <title>${group.title}</title>
</head>
<body class="s2" data-color-scheme="light">
  <main id="root"></main>
  ${reactScripts}
  <script src="../../_ds_bundle.js"></script>
  <script type="text/babel">
    const s2Library = window.${namespace};
    const galleryNames = ${JSON.stringify(group.components)};
    function S2Gallery() {
      return (
        <section className="s2d-gallery">
          {galleryNames.map((componentName) => {
            const S2Component = s2Library[componentName];
            return (
              <article className="s2d-gallery-item" key={componentName}>
                <small>{componentName}</small>
                <S2Component label={componentName} />
              </article>
            );
          })}
        </section>
      );
    }
    ReactDOM.createRoot(document.getElementById("root")).render(<S2Gallery />);
  </script>
</body>
</html>
`;
  write(`components/${group.slug}/${group.slug}.card.html`, card);
}

function foundationCard(file, group, name, subtitle, height, body, bodyAttributes = 'class="s2" data-color-scheme="light"') {
  write(`guidelines/${file}.html`, `<!-- @dsCard group="${group}" viewport="700x${height}" name="${name}" subtitle="${subtitle}" -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="../styles.css">
  <title>${name}</title>
</head>
<body ${bodyAttributes}>
  <main class="ds-card">${body}</main>
</body>
</html>
`);
}

foundationCard('principles', 'Principles', 'Product principles', 'Adaptive, expressive, accessible, and international.', 170, `<div class="ds-row"><span class="ds-chip">Adaptive scale</span><span class="ds-chip">Light · dark</span><span class="ds-chip">Keyboard · touch</span><span class="ds-chip">International</span><span class="ds-chip">Expressive variants</span></div><p class="ds-note">Provider owns locale, color scheme, background layer, and touch scaling.</p>`);
foundationCard('neutral-colors', 'Colors', 'Neutral scale', 'Gray 25–1000 drives layered S2 surfaces and content.', 180, `<div class="ds-grid"><div class="ds-swatch is-light" style="background:var(--s2-gray-25)">Gray 25</div><div class="ds-swatch is-light" style="background:var(--s2-gray-50)">Gray 50</div><div class="ds-swatch is-light" style="background:var(--s2-gray-100)">Gray 100</div><div class="ds-swatch" style="background:var(--s2-gray-500)">Gray 500</div><div class="ds-swatch" style="background:var(--s2-gray-800)">Gray 800</div><div class="ds-swatch" style="background:var(--s2-gray-1000)">Gray 1000</div></div>`);
foundationCard('accent-colors', 'Colors', 'Accent scale', 'S2 blue uses brighter indigo-leaning values than classic Spectrum.', 180, `<div class="ds-grid"><div class="ds-swatch is-light" style="background:var(--s2-blue-100)">Blue 100</div><div class="ds-swatch" style="background:var(--s2-blue-500)">Blue 500</div><div class="ds-swatch" style="background:var(--s2-blue-800)">Blue 800</div><div class="ds-swatch" style="background:var(--s2-blue-900)">Blue 900</div><div class="ds-swatch" style="background:var(--s2-blue-1000)">Blue 1000</div><div class="ds-swatch" style="background:var(--s2-blue-1300)">Blue 1300</div></div>`);
foundationCard('semantic-colors', 'Colors', 'Semantic color', 'Accent, informative, negative, notice, and positive roles.', 180, `<div class="ds-row"><button class="s2d-button s2d-button-accent">Accent</button><button class="s2d-button s2d-button-negative">Negative</button><span class="s2d-status"><i></i>Positive</span><span class="ds-chip" style="color:var(--s2d-notice)">Notice</span><span class="ds-chip" style="color:var(--s2-informative-color-900)">Informative</span></div>`);
foundationCard('extended-palette', 'Colors', 'Extended palette', '18 chromatic scales support data, illustration, and expressive UI.', 180, `<div class="ds-grid"><div class="ds-swatch" style="background:var(--s2-red-900)">Red</div><div class="ds-swatch" style="background:var(--s2-orange-900)">Orange</div><div class="ds-swatch" style="background:var(--s2-green-900)">Green</div><div class="ds-swatch" style="background:var(--s2-cyan-900)">Cyan</div><div class="ds-swatch" style="background:var(--s2-purple-900)">Purple</div><div class="ds-swatch" style="background:var(--s2-magenta-900)">Magenta</div></div>`);
foundationCard('layers-themes', 'Colors', 'Layers and themes', 'Base, layer 1, and layer 2 resolve through light-dark().', 210, `<div class="ds-row" style="align-items:stretch"><section class="ds-layer" style="background:var(--s2-background-base-color)">Base</section><section class="ds-layer" style="background:var(--s2-background-layer-1-color)">Layer 1</section><section class="ds-layer" style="background:var(--s2-background-layer-2-color)">Layer 2</section></div><p class="ds-note">Set data-color-scheme to light or dark; otherwise follow the operating system.</p>`);
foundationCard('type-hierarchy', 'Type', 'Type hierarchy', 'Adobe Clean Spectrum variable fonts with adaptive sizes.', 270, `<div class="ds-type"><span style="font-size:40px;font-weight:800;line-height:1.1">Heading</span><span style="font-size:28px;font-weight:700;line-height:1.2">Title</span><span style="font-size:17px;line-height:1.55">Body text supports longer product explanations.</span><span style="font-size:14px;font-weight:500">UI label</span><code style="font-family:var(--s2d-font-mono)">Source Code Pro</code></div>`);
foundationCard('adaptive-scale', 'Type', 'Adaptive scale', 'Desktop starts at 14 px; touch scales to 17 px and 1.25× geometry.', 190, `<div class="ds-row"><button class="s2d-button s2d-button-secondary" style="min-height:32px">Desktop · 32</button><button class="s2d-button s2d-button-secondary" style="min-height:40px;font-size:17px">Touch · 40</button><span class="ds-note">Media query: not ((hover: hover) and (pointer: fine))</span></div>`);
foundationCard('spacing-scale', 'Spacing', 'Spacing scale', '2–96 px spacing converts to rem; component padding stays px.', 200, `<div class="ds-space"><span style="width:2px;height:12px"></span><span style="width:4px;height:20px"></span><span style="width:8px;height:32px"></span><span style="width:12px;height:48px"></span><span style="width:16px;height:64px"></span><span style="width:24px;height:96px"></span><span style="width:32px;height:128px"></span></div><p class="ds-note">2 · 4 · 8 · 12 · 16 · 24 · 32 px</p>`);
foundationCard('radii', 'Spacing', 'Corner radius', '4, 8, 10, and 16 px surfaces plus pill controls.', 180, `<div class="ds-row"><span class="ds-chip" style="border-radius:4px">Small · 4</span><span class="ds-chip" style="border-radius:8px">Medium · 8</span><span class="ds-chip" style="border-radius:10px">Large · 10</span><span class="ds-chip" style="border-radius:16px">XL · 16</span><button class="s2d-button s2d-button-accent">Pill</button></div>`);
foundationCard('control-sizes', 'Spacing', 'Control sizes', 'T-shirt sizes span 20, 24, 32, 40, and 48 px.', 180, `<div class="ds-row" style="align-items:flex-end"><button class="s2d-button s2d-button-secondary" style="min-height:20px;padding:0 10px;font-size:11px">XS</button><button class="s2d-button s2d-button-secondary" style="min-height:24px;padding:0 12px;font-size:12px">S</button><button class="s2d-button s2d-button-secondary">M</button><button class="s2d-button s2d-button-secondary" style="min-height:40px">L</button><button class="s2d-button s2d-button-secondary" style="min-height:48px">XL</button></div>`);
foundationCard('shadows', 'Effects', 'Elevation', 'Cards and overlays use emphasized, elevated, and dragged shadows.', 180, `<div class="ds-row"><div class="ds-layer" style="box-shadow:0 2px 8px rgb(0 0 0 / .10)">Emphasized</div><div class="ds-layer" style="box-shadow:0 8px 24px rgb(0 0 0 / .16)">Elevated</div><div class="ds-layer" style="box-shadow:0 12px 28px rgb(0 0 0 / .22)">Dragged</div></div>`);
foundationCard('motion', 'Effects', 'Motion', '150 ms default transitions with S2 easing and reduced-motion support.', 170, `<div class="ds-motion"></div><p class="ds-note">cubic-bezier(0.45, 0, 0.4, 1)</p>`);
foundationCard('expressive-gradients', 'Effects', 'Expressive variants', 'Premium and gen-AI buttons use source-defined multicolor gradients.', 180, `<div class="ds-row"><button class="s2d-button s2d-button-premium">Premium</button><button class="s2d-button s2d-button-genai">Generate</button><span class="ds-note">Gradients are intentional variants, not page decoration.</span></div>`);
foundationCard('iconography', 'Brand', 'Iconography', '48 UI glyphs and 410 workflow icons copied from S2.', 190, `<div class="ds-icons"><img src="../assets/ui-icons/S2_CheckmarkSize200.svg" alt="Checkmark"><img src="../assets/ui-icons/S2_CrossSize200.svg" alt="Cross"><img src="../assets/ui-icons/S2_ChevronSize200.svg" alt="Chevron"><img src="../assets/ui-icons/S2_DragHandleSize200.svg" alt="Drag handle"><img src="../assets/workflow-icons/S2_Icon_Add_20_N.svg" alt="Add"><img src="../assets/workflow-icons/S2_Icon_Search_20_N.svg" alt="Search"><img src="../assets/workflow-icons/S2_Icon_Settings_20_N.svg" alt="Settings"><img src="../assets/workflow-icons/S2_Icon_User_20_N.svg" alt="User"></div>`);
foundationCard('illustrations', 'Brand', 'Illustrations', 'All 518 public illustration families copied at the 96 px source size.', 220, `<div class="ds-illustrations"><img src="../assets/illustrations/linear/S2_lin_AIGenerate_96.svg" alt="AI generate linear"><img src="../assets/illustrations/gradient/generic1/S2_fill_AIGenerate_generic1_96.svg" alt="AI generate gradient one"><img src="../assets/illustrations/linear/S2_lin_alertNotice_96.svg" alt="Alert notice linear"><img src="../assets/illustrations/gradient/generic2/S2_fill_AIGenerate_generic2_96.svg" alt="AI generate gradient two"></div>`);

const inventoryMarkdown = groups.map(group => `- **${group.title}:** ${group.components.join(', ')}`).join('\n');
write('readme.md', `# React Spectrum 2 / S2 Design System

Spectrum 2（S2）是 Adobe 新一代设计语言和 React 组件系统。本目录独立导入 \`@react-spectrum/s2@1.6.0\` 的公共视觉 API、\`@adobe/spectrum-tokens@14.15.0\`、图标与插画，供设计代理和原型使用。

## 术语与命名

- **Spectrum 2 / S2：** 本目录描述的新设计系统；包名 \`@react-spectrum/s2\`。
- **React Spectrum 3 / RSP3：** 经典 React Spectrum 系统；保存在相邻 \`designs/react-spectrum3\`，不混入本目录。
- **Design component：** 面向原型的轻量视觉复刻；不是上游生产实现。
- **Provider：** locale、color scheme、background layer、router 与自适应缩放的根容器。
- **Style macro：** S2 生产源码的类型化样式入口；本导入把可验证 token 映射为 CSS custom properties，便于静态原型消费。

## 目标

让后续设计只从本目录读取 S2 的视觉语言、token、组件名和资产；让 S2 与 RSP3 能并排审阅。生产代码继续使用上游包，保留完整可访问性、状态管理、国际化和 style macro 编译行为。

## 结构

- \`styles.css\`：唯一 CSS 入口，只含 \`@import\`。
- \`tokens/\`：2469 个固定版本源 token、S2 page/theme 变量、官方远程字体声明和语义别名。
- \`components/\`：137 个公共视觉导出，含原型组件、props 契约、提示和 9 张分组卡。
- \`guidelines/\`：16 张颜色、字体、间距、效果、图标和插画基础卡。
- \`assets/\`：48 个 UI SVG、410 个 workflow SVG、518 个公开插画家族的 96 px SVG。
- \`sources/\`：固定版本 token JSON、包元数据和公共组件清单。
- \`tools/regenerate.mjs\`：清单、token 转换和机械生成内容的唯一事实源。

## 功能

- 提供可加载的 S2 token、组件、卡片和单文件总览。
- 支持 light、dark 与系统色彩模式。
- 按输入能力切换 desktop/touch 字号和几何缩放。
- 提供 accent、negative、premium、gen-AI 等源定义视觉角色。
- 让设计代理按公共 API 名称组合 S2 原型。

## 实体、属性

- **Token：** 名称唯一；值来自 \`variables.json\`。light/dark 用 \`light-dark()\`；desktop/mobile 用源 media query 覆盖。
- **Component：** PascalCase 公共名唯一；每个组件具备 \`.jsx\`、\`.d.ts\`、\`.prompt.md\`。
- **Card：** 首行 \`@dsCard\` 决定分组、名称和 viewport。
- **Asset：** 保留上游文件名；图标不从记忆重画。
- **Illustration family：** linear、gradient/generic1、gradient/generic2；本目录保留每个公共家族的 M/96 px 原文件。

## 关系

\`styles.css\` 导入 source token、Provider page 变量和共享原型样式；组件只消费这些变量。分组卡从 \`_ds_bundle.js\` 读取同一实现。\`preview.html\` 由 compiler 从 README、cards 和 manifest 生成。

## 状态

- Color scheme：system、light、dark。
- Background：base、layer-1、layer-2。
- Scale：desktop \`--s2-scale: 1\`；touch \`1.25\`。
- Interaction：default、hover、focus-visible、pressed、selected、disabled、invalid。
- Variant：primary、secondary、accent、negative、premium、gen-AI、quiet。
- Motion：默认 150 ms；遵守 \`prefers-reduced-motion\`。

## 界限

- 本目录是设计与原型约束，不替代 \`@react-spectrum/s2\` 生产包。
- 不包含 RSP3 视觉 token、React Aria hooks、解析器或 drag/drop 常量。
- 字体 CSS 来自 S2 源码，但字体二进制由 Adobe Typekit 远程提供；离线时回退系统字体。
- 上游是组件库，不是可确认的产品应用，因此不凭空创建 UI kit 或 starting point。
- 组件卡验证视觉结构；复杂键盘导航、screen reader 语义、virtualization、locale 和 style macro 逻辑以上游实现为准。
- 插画每个公共家族只复制 96 px 源文件；生产包仍提供 48/96/160 px。

## Content fundamentals

使用直接、任务导向、sentence case 文案。标签说明对象，按钮使用短动词，如 “Save”“Share”“Generate”。帮助文案解释下一步。错误说明问题并给出修复动作。Emoji 不充当控件图标；生产字符串走国际化资源。

## Visual foundations

S2 使用更亮的 indigo-blue accent、更宽的色阶和 light/dark 原生组合。基础表面从 gray 25、50、75 构建；字段用 2 px 边界和 8 px 圆角；卡片默认 10 px；重点表面可到 16 px；按钮保持 pill。控件尺寸为 20、24、32、40、48 px，触摸设备整体放大 1.25×。卡片和 overlay 比 RSP3 更强调层级和阴影。Premium 与 gen-AI 渐变仅用于明确变体。Hover/press 改变颜色并允许轻微位移；focus ring 始终可见。布局使用 Flex/Grid 与显式 gap。

## Iconography

S2 内置 48 个结构型 UI glyph 和 410 个 20 px workflow SVG。控制图标使用这些源文件，不使用 emoji 或 Unicode 字符替代。518 个公开插画家族分为 linear 与两个 gradient theme；本目录复制所有家族的 96 px SVG。未提供独立 Adobe logo，因此不造 logo。

## 与 React Spectrum 3 的差异

| 维度 | Spectrum 2 / S2 | React Spectrum 3 |
| --- | --- | --- |
| 包版本 | \`@react-spectrum/s2@1.6.0\` | \`@adobe/react-spectrum@3.47.3\` |
| 公共视觉导出 | 137 | 101 |
| 样式模型 | Type-safe style macro + \`light-dark()\` | Spectrum CSS classes + theme/scale CSS |
| 基础字号 | Desktop 14；touch 17 | Medium/large scale token 体系 |
| 控件尺寸 | 20/24/32/40/48 px | 经典 medium 常见 32；large 常见 40 px |
| 圆角 | 4/8/10/16 px + pill | 经典字段/表面多为 4–6 px + pill |
| Accent | 更亮的 indigo-blue，900 为 light \`rgb(59, 99, 251)\` | 经典 Spectrum blue 900 为 \`#0265dc\` |
| 表面 | 分层更强、卡片阴影更明显 | 边界更克制、表面更紧凑 |
| 表达性 | Premium、gen-AI 渐变为正式变体 | 默认不以表达性渐变为核心 |
| 资产 | 458 个 SVG 图标；518 个插画家族 | 本地经典快照资产较少 |

## Component inventory

公共视觉导出以 \`packages/@react-spectrum/s2/exports/index.ts\` 为唯一清单，共 137 个：

${inventoryMarkdown}

## Intentional addition

\`components/shared/s2Primitive.jsx\` 是导入层唯一 helper，用于 DRY 地生成轻量视觉预览；它不是 S2 公共 API。

## 索引与验证

- 单文件总览：\`preview.html\`
- 机器清单：\`_ds_manifest.json\`
- 运行时 bundle：\`_ds_bundle.js\`
- Adherence 规则：\`_adherence.oxlintrc.json\`
- 再生成：\`node tools/regenerate.mjs\`，随后运行 compiler、checker 和 preview builder。

## 参考文档与引用

- 本地源：\`${upstreamRoot}\`
- 公共导出：\`${upstreamRoot}\\packages\\@react-spectrum\\s2\\exports\\index.ts\`
- S2 styling：\`${upstreamRoot}\\packages\\@react-spectrum\\s2\\style\\spectrum-theme.ts\`
- 上游仓库：https://github.com/adobe/react-spectrum
- 上游文档：https://react-spectrum.adobe.com/s2/
- 包版本：\`@react-spectrum/s2@1.6.0\`
- Token 版本：\`@adobe/spectrum-tokens@14.15.0\`
- 许可：Apache-2.0；见 \`LICENSE.source.txt\`、\`NOTICE.source.txt\` 和 \`SPECTRUM-TOKENS-LICENSE.source.txt\`。
- 上游 Git commit 不在此解压快照中，无法可靠记录。
`);

write('SKILL.md', `---
name: react-spectrum-s2-design
description: Use this skill to generate Spectrum 2 interfaces and design artifacts with verified S2 tokens, the public component inventory, content rules, icons, and illustrations.
user-invocable: true
---

Read \`readme.md\` first. Treat it, \`styles.css\`, and \`tokens/\` as binding visual constraints.

For visual artifacts, copy only needed assets and build static HTML from the listed tokens and components. For production code, use \`@react-spectrum/s2\`; the local JSX files are cosmetic prototypes, not production accessibility implementations.

If invoked without a concrete artifact request, ask what interface or asset to create, its target viewport, and whether light, dark, desktop, or touch behavior matters.
`);

function annotateUnclassifiedTokens() {
  const tokenFiles = ['tokens/page.css', 'tokens/s2-tokens.css', 'tokens/semantic.css', 'components/components.css', 'guidelines/cards.css'];
  const declarationPattern = /(--[A-Za-z0-9-]+)\s*:\s*([^;]+);[ \t]*(?:\/\*\s*@kind\s+([A-Za-z]+)\s*\*\/)?/g;
  const values = new Map();
  for (const relativePath of tokenFiles) {
    const css = fs.readFileSync(path.join(root, relativePath), 'utf8');
    for (const match of css.matchAll(declarationPattern)) if (!match[2].includes('{') && !match[2].includes('}')) values.set(match[1], match[2].trim());
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
    const hasColor = /#[0-9a-fA-F]{3,8}\b/.test(resolved) || /\b(rgba?|hsla?|okl?ch|oklab|lab|lch|hwb|color|color-mix)\(/.test(resolved) || (/\blight-dark\(/.test(resolved) && /#|rgb|hsl|okl?ch|lab|lch|color\(/.test(resolved)) || ['transparent', 'currentcolor', 'black', 'white', 'red', 'green', 'blue', 'gray', 'grey'].includes(resolved.toLowerCase());
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

console.log(`Generated Spectrum 2 authoring sources: ${allComponents.length} components, ${groups.length} component cards, 16 foundation cards, 2469 source tokens. Namespace: ${namespace}`);
