import type {ReactElement, ReactNode} from 'react';

export interface DisclosureProps {
  children?: ReactNode;
  isExpanded?: boolean;
  defaultExpanded?: boolean;
  onExpandedChange?: (isExpanded: boolean) => void;
}

export declare function Disclosure(props: DisclosureProps): ReactElement;
