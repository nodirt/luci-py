// Copyright 2014 The Swarming Authors. All rights reserved.
// Use of this source code is governed by the Apache v2.0 license that can be
// found in the LICENSE file.

var config_page = (function() {
var exports = {};


// Fetches the importer config from the server.
var readImporterConfig = function() {
  return api.call('GET', '/auth_service/api/v1/importer/config');
};


// Pushes config to the server.
var writeImporterConfig = function(config) {
  return api.call('POST', '/auth_service/api/v1/importer/config', config);
};


// Called when HTML body of a page is loaded.
exports.onContentLoaded = function() {

  // Show alert box with operation result, enable back UI.
  var showResult = function(type, title, message) {
    $('#import-config-alerts').html(
        common.getAlertBoxHtml(type, title, message));
    common.setInteractionDisabled($('#import-config'), false);
  };

  // Handle 'Save' button.
  $('#import-config').submit(function(event) {
    event.preventDefault();
    var config = null;
    try {
      config = JSON.parse($('#import-config textarea[name="config"]').val())
    } catch(err) {
      showResult('error', 'Bad JSON.', err.message);
      return;
    }
    common.setInteractionDisabled($('#import-config'), true);
    writeImporterConfig({'config': config}).then(function(response) {
      showResult('success', 'Config updated.');
    }, function(error) {
      showResult('error', 'Oh snap!', error.text);
    });
  });


  // Read the config, show the page only when it's available.
  readImporterConfig().then(function(response) {
    var str = JSON.stringify(response.data['config'], undefined, 2);
    $('#import-config textarea[name="config"]').val(str);
    common.presentContent();
  }, function(error) {
    common.presentError(error.text);
  });
};


return exports;
}());
