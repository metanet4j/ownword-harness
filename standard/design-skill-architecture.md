# OwnWord Design Skill Architecture

## Purpose

OwnWord 的设计能力分为产品设计、设计方法、视觉表达和组件实现四个层级。不同能力保持职责边界，避免重复定义。

## Skill Layers

```text
ownword-design-principles
        ↓
baoyu-design
        ↓
design-taste-frontend
        ↓
react-spectrum
```

## Responsibility Boundary

### ownword-design-principles

定义 OwnWord 产品和品牌层面的设计约束，包括身份表达、内容关系和体验原则。

### baoyu-design

提供通用设计方法，包括设计分析、设计系统意识、视觉质量判断和原型验证方法。

### design-taste-frontend

负责页面视觉方向和前端设计执行，包括设计语言判断、布局、动效和反模板化约束。

### react-spectrum

负责组件实现规范，包括组件选择、Design Token、交互状态和无障碍要求。

## Usage Rule

设计方向和产品表达由上层设计能力决定，React Spectrum 用于实现通用组件和交互能力。品牌展示区域和特殊内容布局可以使用自定义设计实现。