// Tiny icon components — flat strokes, monochrome
const Icon = ({ d, size=14, fill='none', strokeWidth=1.6, ...rest }) => (
  <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" {...rest}>
    {d}
  </svg>
);
const IconEvent = (p) => <Icon {...p} d={<><path d="M4 8h16M6 4v3M18 4v3M5 8h14v12H5z"/><circle cx="9" cy="13" r="0.6" fill="currentColor"/><circle cx="13" cy="13" r="0.6" fill="currentColor"/><circle cx="17" cy="13" r="0.6" fill="currentColor"/></>} />;
const IconLandmark = (p) => <Icon {...p} d={<><path d="M3 21h18M5 21V10M19 21V10M9 21V10M15 21V10M3 10h18L12 4 3 10z"/></>} />;
const IconFork = (p) => <Icon {...p} d={<><path d="M8 4v6a3 3 0 0 0 6 0V4M11 13v7M16 4v8h2v8M18 4l-2 8"/></>} />;
const IconSpark = (p) => <Icon {...p} d={<><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></>} />;
const IconLink = (p) => <Icon {...p} d={<><path d="M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1M14 10a4 4 0 0 0-5.66 0l-3 3a4 4 0 0 0 5.66 5.66l1-1"/></>} />;
const IconArrowRight = (p) => <Icon {...p} d={<><path d="M5 12h14M13 5l7 7-7 7"/></>} />;
const IconRefresh = (p) => <Icon {...p} d={<><path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5"/></>} />;
const IconReset = (p) => <Icon {...p} d={<><path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5"/></>} />;
const IconDownload = (p) => <Icon {...p} d={<><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></>} />;
const IconCheck = (p) => <Icon {...p} d={<><path d="M5 13l4 4L19 7"/></>} />;
const IconClock = (p) => <Icon {...p} d={<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>} />;
const IconWand = (p) => <Icon {...p} d={<><path d="M14 7l3 3M5 21l9-9M3 5l1 1M19 17l1 1M16 3l1 2 2 1-2 1-1 2-1-2-2-1 2-1z"/></>} />;
const IconChat = (p) => <Icon {...p} d={<><path d="M4 6h16v10H8l-4 4V6z"/></>} />;
const IconCpu = (p) => <Icon {...p} d={<><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/><rect x="10" y="10" width="4" height="4"/></>} />;
const IconWarn = (p) => <Icon {...p} d={<><path d="M12 3l10 18H2L12 3zM12 10v5M12 18v.5"/></>} />;
const IconInbox = (p) => <Icon {...p} d={<><path d="M3 13l2-8h14l2 8M3 13v6h18v-6M3 13h6l1 2h4l1-2h6"/></>} />;

window.DION_ICONS = { IconEvent, IconLandmark, IconFork, IconSpark, IconLink, IconArrowRight, IconRefresh, IconReset, IconDownload, IconCheck, IconClock, IconWand, IconChat, IconCpu, IconWarn, IconInbox };
