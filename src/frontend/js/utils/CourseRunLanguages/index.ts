import { CourseRun } from 'types';

export const IsAllCourseRunsWithSameLanguages = (courseRuns: CourseRun[]) => {
  const languages = courseRuns[0].languages.sort();
  for (let i = 1; i < courseRuns.length; i++) {
    const runLanguages = courseRuns[i].languages.sort();
    if (
      !(runLanguages.length === languages.length) ||
      !runLanguages.every((value, index) => value === languages[index])
    ) {
      return false;
    }
  }
  return true;
};
