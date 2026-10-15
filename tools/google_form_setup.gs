/**
 * One-time setup for Ramu's website news: creates the Google Form, its response Sheet,
 * and a "Show" column used to approve items for the website.
 *
 * How to use (about 2 minutes):
 *   1. Go to https://script.google.com and click "New project".
 *   2. Delete the sample code, paste this whole file, and click Save.
 *   3. Click Run (with "setup" selected). Approve the permission prompt
 *      (it asks to create a form and a spreadsheet in your Google Drive).
 *   4. Open "Execution log": it prints the form link (share with family) and the sheet link.
 */
function setup() {
  var form = FormApp.create('Ramu Maharajapuram – website update');
  form.setDescription(
    'Share news for Ramu\'s website: concerts, new songs or videos, TV appearances, awards. ' +
    'Items appear on the website after they are approved.');
  form.setCollectEmail(false);
  form.setConfirmationMessage('Thank you! The update will appear on the website once it is approved.');

  form.addMultipleChoiceItem().setTitle('What is it?')
    .setChoiceValues(['Concert', 'New song or video', 'TV or interview', 'Award or honour', 'Other'])
    .setRequired(true);
  form.addTextItem().setTitle('Title')
    .setHelpText('For example: SPB Night with Ramu, Dallas').setRequired(true);
  form.addDateItem().setTitle('Date')
    .setHelpText('The day of the concert, release or event').setRequired(true);
  form.addTextItem().setTitle('City and venue');
  form.addParagraphTextItem().setTitle('Details')
    .setHelpText('Anything visitors should know: time, orchestra, co-singers, where to buy tickets');
  form.addTextItem().setTitle('Link')
    .setHelpText('Optional: YouTube, Facebook, poster or ticket link');
  form.addTextItem().setTitle('Your name').setRequired(true);

  var ss = SpreadsheetApp.create('Ramu website – updates');
  ss.setSpreadsheetLocale('en_US');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
  Utilities.sleep(3000);

  // The form writes to a sheet named like "Form Responses 1".
  var sheet = ss.getSheets().filter(function (s) { return s.getFormUrl(); })[0] || ss.getSheets()[0];
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var showCol = headers.length + 1;
  sheet.getRange(1, showCol).setValue('Show').setFontWeight('bold');
  sheet.getRange(2, showCol, 1000, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['Yes', 'No'], true).build());

  // Dates as 2026-11-08 so the website reads them the same everywhere.
  var dateCol = headers.indexOf('Date') + 1;
  if (dateCol > 0) sheet.getRange(2, dateCol, 1000, 1).setNumberFormat('yyyy-mm-dd');

  // Remove the empty default "Sheet1" if the form created its own sheet.
  ss.getSheets().forEach(function (s) {
    if (s.getName() === 'Sheet1' && !s.getFormUrl() && ss.getSheets().length > 1) ss.deleteSheet(s);
  });

  Logger.log('FORM to share with family:  ' + form.getPublishedUrl());
  Logger.log('SHEET (approve rows here):  ' + ss.getUrl());
  Logger.log('Next: in the sheet, File → Share → Publish to web → "' + sheet.getName() +
             '" → Comma-separated values (.csv) → Publish, and send that link to update the website.');
}
