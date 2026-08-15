import type {ReactElement, ReactNode} from 'react';

export interface BreadcrumbsProps {
  children?: ReactNode;
  isDisabled?: boolean;
}

export declare function Breadcrumbs(props: BreadcrumbsProps): ReactElement;
