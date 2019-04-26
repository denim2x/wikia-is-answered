'use strict';

const type = require('type-of');
const request = require('superagent');
const h = require('hyperscript-string');
const $ = require('domtastic');
const rivets = require('rivets');

$.fn.innerText = function(value) {
  if (value === undefined) {
    return this[0].innerText;
  }

  return this.forEach(function(element) {
    return element.innerText = '' + value;
  });
};

$.fn.clear = function() {
  this.forEach((e) => {
    e.innerHTML = '';
  });
  return this;
};

$.fn.outerHTML = function() {
  return this.prop('outerHTML');
};

const state = {
  message: '',
  knowledge: [],
  conversation: [],
  error: false
};

function _error(method, url, { response: res }) {
  res = res ? [res.status, res.text] : [];
  console.warn(`[${method} ${url}]`, ...res);
}

function get_knowledge() {
  request.get('/knowledge').then(({ body }) => {
    state.knowledge = body;
  }, (e) => _error('GET', '/knowledge', e));
}

function send_message(text='', cb) {
  request.post('/respond').send(text).then(({ body }) => {
    state.conversation.push({ text: body[0] });
  }, (e) => { 
    _error('POST', '/respond', e);
    if (cb) {
      cb();
    }
  });
}

send_message();
get_knowledge();

$('.Conversation-input')
  .on('keydown', (e) => {
    let message = state.message;
    if (e.code == 'Enter' && !e.shiftKey && !e.altKey && !e.ctrlKey) {
      if (message == '')
        return;
      state.message = '';
      state.conversation.push({ text: message, is_user: true });
      send_message(message, () => { state.error = true; });
      get_knowledge();
      return false;
    }
  })
  .on('paste', (e) => {
    e.preventDefault();
    let text = e.clipboardData.getData("text/plain");
    document.execCommand("insertHTML", false, text);
    return false;
  });

function _const(self, key, value) {
  Object.defineProperty(self, key, {
    value, writable: false, enumerable: true, configurable: true
  });
  return self;
}

const { Binding } = rivets._;
rivets._.Binding = class extends Binding {
  parseTarget() {
    if (this.binder.parseTarget) {
      Object.assign(this, this.binder.parseTarget(this.keypath));
    }
    return super.parseTarget();
  }

  publish() {
    _const(this, 'state', 'publish');
    let ret = super.publish();
    _const(this, 'state');
  }
};

rivets.binders['input'] = {
  parseTarget(keypath) {
    let empty_class;
    [keypath, empty_class] = keypath.trim().split(/\s*\?\s*/);
    return { keypath, empty_class };
  },

  bind: function(el) {
    $(el).on('input.rivets', this.publish);
  },

  unbind: function(el) {
    $(el).off('input.rivets');
  },

  routine: function(el, value) {
    if (this.state != 'publish') {
      el.innerText = value;
    }
    state.error = false;  
    if (this.empty_class) {
      $(el).toggleClass(this.empty_class, value == '');
    }
  },

  getValue : function(el) {
    return el.innerText.trim();
  }
};

global.$state = state;

rivets.bind(document.body, state);
