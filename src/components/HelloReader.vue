<template>
  <v-app id="inspire">
    <v-app-bar
      class="px-3"
      density="compact"
      flat
    >
      <v-spacer></v-spacer>
      <div>PodCastReader</div>
      <v-spacer></v-spacer>
    </v-app-bar>

    <v-main class="bg-grey-lighten-3">
      <v-container>
        <!-- 移动端：单栏切换布局 -->
        <div>
          <!-- Feed列表视图 -->
          <div v-show="mobileTab === 'feeds'">
            <v-card rounded="lg">
              <v-list>
                <v-list-item
                  title="FeedList"
                ></v-list-item>
                <v-divider></v-divider>
                <v-list-item
                  v-for="item in podlist"
                  :key="item.title"
                  :title="item.title"
                  :value="item.value"
                  @click="onPodlistClick(item); mobileTab = 'episodes'"
                >
                </v-list-item>
              </v-list>
            </v-card>
          </div>

          <!-- Episode列表视图 -->
          <div v-show="mobileTab === 'episodes'">
            <v-card rounded="lg">
              <v-list :max-height="calcMobileHeight()" style="overflow-y: auto;">
                <v-list-item
                  title="EpisodeList"
                ></v-list-item>
                <v-divider></v-divider>
                <v-list-item
                  v-for="item in itemlist"
                  :key="item.title"
                  :title="item.title"
                  :value="item.value"
                  @click="onItemlistClick(item); mobileTab = 'player'"
                >
                </v-list-item>
              </v-list>
            </v-card>
          </div>

          <!-- 播放器和字幕视图 -->
          <div v-show="mobileTab === 'player'" class="mobile-player-container">
            <v-sheet
              :min-height="calcMobileHeight()"
              rounded="lg"
              class="pa-3"
            >
              <h2 class="text-h6">{{ cur_item.title }}</h2>
              <p class="text-caption">{{ cur_item.pubdate }}</p>
              <p class="text-body-2" v-html="cur_item.description"></p>
              <br>
              <h2 v-if="(subtitle.length == 0)&&(cur_item.title!=undefined)" class="text-body-1">未能找到字幕，请通过后台生成。</h2>
              <div class="container100">
                <template v-for="sub in subtitle">
                  <p :id="`mobile-sub${sub.start}`" class="text-caption clickable-time" @click="seekToTime(sub.start)">
                    {{ sub.interval }}
                  </p>
                  <blockquote :id="`mobile-subtitle${sub.start}`" class="text-body-2">
                    <template v-for="(word, index) in parseWords(sub.text)" :key="index">
                      <span
                        v-if="word.isWord"
                        class="clickable-word"
                        @click="lookupWord(word.text)"
                      >{{ word.text }}</span>
                      <span v-else>{{ word.text }}</span>
                    </template>
                  </blockquote>
                </template>
              </div>
            </v-sheet>
          </div>
        </div>
      </v-container>
    </v-main>

    <!-- 底部导航 -->
    <v-bottom-navigation
      v-model="mobileTab"
      color="primary"
      grow
      height="56"
    >
      <v-btn value="feeds">
        <v-icon>mdi-rss</v-icon>
        <span>Feeds</span>
      </v-btn>

      <v-btn value="episodes">
        <v-icon>mdi-playlist-play</v-icon>
        <span>Episodes</span>
      </v-btn>

      <v-btn value="player">
        <v-icon>mdi-play-circle</v-icon>
        <span>Player</span>
      </v-btn>
    </v-bottom-navigation>

    <!-- 播放器固定在底部 -->
    <v-footer
      height="120"
      app
    >
      <div class="element-of-your-choice audioplayer">
        <p>shikwasa播放器占位</p>
      </div>
    </v-footer>

    <!-- 单词查询结果 Snackbar -->
    <v-snackbar
      v-model="wordLookup.snackbar"
      :timeout="5000"
      location="top"
      color="white"
    >
      <div v-html="wordLookup.content"></div>
      <template v-slot:actions>
        <v-btn variant="text" @click="wordLookup.snackbar = false">
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>




<script setup>

import axios from 'axios'
import {parseOPML} from '@/utils/opml'
import { extractFromXml } from '@extractus/feed-extractor'
import CryptoJS from 'crypto-js';

import { ref, nextTick } from 'vue'
import { useDisplay } from 'vuetify'

//const audioElement = ref(null);
let  audioplayer = null;

let podlist = ref([])
let itemlist = ref([])
let cur_item = ref({})
let cur_pod = {}
let audiosrc = ref('')
let audio_original_src = ref('')
let subtitle = ref([])
let current_subtitle = null
let cur_folder = ''
let dict_url = 'https://www.wotiku.cn/ecdict/dict/';

// 移动端底部导航状态
const mobileTab = ref('feeds')

// 单词查询状态
const wordLookup = ref({
  snackbar: false,
  content: '',
  timeout: 0, // 手动关闭
})

import 'shikwasa/dist/style.css'
import { Player } from 'shikwasa'



document.addEventListener('DOMContentLoaded', () => {
  audioplayer = new Player({
    container: () => document.querySelector('.element-of-your-choice'),
    themeColor: '#000000',
    audio: {
      title: 'Hello World!',
      artist: 'Shikwasa FM',
      cover: 'image.png',
      src: 'audio.mp3',
    },
  });
  audioplayer.on('timeupdate',() => {
    if (audioplayer) {
      let currentTime = audioplayer.currentTime;
      console.log(currentTime)
      if(current_subtitle==null || (current_subtitle.end<currentTime || currentTime<current_subtitle.start)){
        console.log('字幕查询')
        current_subtitle = findSubtitle(subtitle.value, currentTime);
        if (current_subtitle) {
            console.log('找到字幕:', current_subtitle);
            console.log('字幕文本:', current_subtitle.text);
            console.log('字幕数组长度:', subtitle.value.length);

            const prefix = 'mobile-subtitle';

            console.log('准备滚动到元素:', prefix + current_subtitle.start);

            // 滚动到blockquote元素（字幕文本）
            let elementId = `${prefix}${current_subtitle.start}`;
            let element = document.getElementById(elementId);
            console.log('元素是否存在:', element !== null);
            console.log('元素尺寸:', element ? element.offsetWidth + 'x' + element.offsetHeight : 'N/A');
            console.log('元素文本内容:', element ? element.textContent.substring(0, 20) : 'N/A');

            //滚动到对应字幕 - 使用nextTick确保DOM已更新
            nextTick(() => {
              scrollToElementCenter(elementId)
            })

            // 移除所有加粗
            document.querySelectorAll('blockquote[id^="mobile-subtitle"]').forEach(blockquote => {
              blockquote.classList.remove('bold-text');
            })
            document.getElementById(elementId).classList.add('bold-text');
        } else {
            console.log('当前时间: ' + currentTime + ', 无字幕显示');
            // 在这里清除或隐藏字幕
        }
      }else{
        console.log('字幕查询skip')
      }
    }
  });
  audioplayer.on('error',()=>{
    console.log(cur_item.value.title,cur_pod.title,cur_pod.imageurl,audio_original_src.value);
    audioplayer.update({
        title: cur_item.value.title,
        artist: cur_pod.title,
        cover: cur_pod.imageurl,
        src: audio_original_src.value
    })
  });
});


// 初始化
initMain()

// 初始化
function initMain(){
  //读取public/data/base.opml文件
  axios.get('data/base.opml').then(response => {
    const baseopml = response.data
    //console.log(baseopml)
    let opmljson = parseOPML(baseopml)
    console.log(opmljson)
    opmljson.forEach(element => {
      podlist.value.push({
        title: element.title,
        value: element.xmlUrl})
    });
  })
  itemlist.value = [];
}

function test() {
  axios.get('http://127.0.0.1/ollama/api/tags').then(response => {
    const tags = response.data
    console.log(tags)
  })
}

//点击podlist时触发
async function  onPodlistClick(item){
  console.log(item)
  itemlist.value = [];
  cur_pod.title = item.title
  //将value编码为md5
  const md5Hash = CryptoJS.MD5(item.title).toString();
  cur_folder = md5Hash;
  axios.get(`data/rss/${md5Hash}`).then(response => {
    const rss = response.data
    const feed = extractFromXml(rss,{useISODateFormat: false,
      getExtraFeedFields: (feedData) => {
        return {
          image: feedData.image || '',
          itunes:feedData['itunes:image'] || '',
        }
      },
      getExtraEntryFields: (feedEntry) => {
        const {
          enclosure
        } = feedEntry
        return {
          enclosure: {
            url: enclosure['@_url'],
            type: enclosure['@_type'],
            length: enclosure['@_length']
          }
        }
      }
    })
    //解析feed
    console.log(feed)
    if (feed.image) {
      cur_pod.imageurl=feed.image.url;
    } else if(feed.itunes) {
      cur_pod.imageurl=feed.itunes['@_href'];
    }else{
      cur_pod.imageurl='';
    }
    cur_pod.image=feed.image;
    feed.entries=feed.entries.slice(0, 100);
    feed.entries.forEach(element => {
      //console.log(element);
      if (element.link.toLowerCase().endsWith('.mp3')) {
        itemlist.value.push({
          title: element.title,
          description: element.description,
          pubdate: element.published,
          value: element.link})
      } else{
        itemlist.value.push({
          title: element.title,
          description: element.description,
          pubdate: element.published,
          value: element.enclosure.url})
      }
    });
    //console.log(itemlist.value)
  })
}

//点击itemlist时触发
function  onItemlistClick(item){
  cur_item.value = item
  console.log(item)
  audio_original_src.value = item.value
  //CryptoJS.MD5(item.title).toString()
  audiosrc.value = `data/mp3/${cur_folder}/${CryptoJS.MD5(item.title).toString()}.mp3`
  // nextTick(() => {
  //   // 重置音频元素
  //   audioElement.value.load();
  // });
  //audioElement.value.load();
  handleSubtitles(`data/subtitles/${cur_folder}/${CryptoJS.MD5(item.title).toString()}.json`);
  audioplayer.update({
      title: item.title,
      artist: cur_pod.title,
      cover: cur_pod.imageurl,
      src: `data/mp3/${cur_folder}/${CryptoJS.MD5(item.title).toString()}.mp3`
  })
}

// function handleAudioError() {
//   console.log('音频加载失败，重新设置音频源')
//   audiosrc.value = audio_original_src.value;
//   nextTick(() => {
//     // 重置音频元素
//     audioElement.value.load();
//   });
// }

//处理播客脚本显示
function handleSubtitles(filepath){
  axios.get(filepath).then(response => {
    const json = response.data
    if (typeof(json) == 'object'){
      subtitle.value = json
    }else{
      subtitle.value = []
    }
  }).catch(error=>{
    subtitle.value = []
  })
}


// 使用二分查找找到当前时间对应的字幕
function findSubtitle(subtitles, currentTime) {
    var left = 0;
    var right = subtitles.length - 1;
    while (left <= right) {
        var mid = Math.floor((left + right) / 2);
        if (subtitles[mid].start <= currentTime && currentTime <= subtitles[mid].end) {
            return subtitles[mid];
        } else if (currentTime < subtitles[mid].start) {
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    return null;
}

//
// function handleTimeUpdate() {
//   if (audioElement.value) {
//     let currentTime = audioElement.value.currentTime;
//     console.log(currentTime)
//     if(current_subtitle==null || (current_subtitle.end<currentTime || currentTime<current_subtitle.start)){
//       console.log('字幕查询')
//       current_subtitle = findSubtitle(subtitle.value, currentTime);
//     }else{
//       console.log('字幕查询skip')
//     }
//     if (current_subtitle) {
//         //滚动到对应字幕
//         //document.getElementById(`sub${currentSubtitle.start}`).scrollIntoView();
//         scrollToElementCenter(`sub${current_subtitle.start}`)
//         document.querySelectorAll('blockquote').forEach(blockquote => {
//           blockquote.classList.remove('bold-text');
//         })
//         document.getElementById(`subtitle${current_subtitle.start}`).classList.add('bold-text');
//     } else {
//         console.log('当前时间: ' + currentTime + ', 无字幕显示');
//         // 在这里清除或隐藏字幕
//     }
//   }
// }

// 假设元素的ID为"elementId"
function scrollToElementCenter(elementId) {
  // 获取元素
  var element = document.getElementById(elementId);

  if (!element) {
    console.log('元素未找到:', elementId);
    return;
  }

  // 滚动到元素位置（减去视口1/3）
  var viewportHeight = window.innerHeight || document.documentElement.clientHeight;
  var elementRect = element.getBoundingClientRect();
  var scrollPosition = window.pageYOffset + elementRect.top - (viewportHeight / 3);

  window.scrollTo({
    top: scrollPosition,
    behavior: 'smooth'
  });
}

// 计算移动端内容区域高度
function calcMobileHeight() {
  // 视口高度 - app-bar - 底部导航 - 播放控件 - container padding
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight
  const appBarHeight = 48 // compact app-bar height
  const bottomNavHeight = 56 // v-bottom-nav height
  const playerHeight = 120 // v-footer height (播放控件)
  const padding = 24 // container padding
  return (viewportHeight - appBarHeight - bottomNavHeight - playerHeight - padding) + 'px'
}

// 解析文本为单词和非单词部分
function parseWords(text) {
  // 使用正则表达式匹配单词（字母、数字、连字符、撇号）
  const regex = /([a-zA-Z0-9'-]+)|([^a-zA-Z0-9'-]+)/g
  const matches = []
  let match

  while ((match = regex.exec(text)) !== null) {
    if (match[1]) {
      // 单词部分
      matches.push({
        text: match[1],
        isWord: true
      })
    } else if (match[2]) {
      // 非单词部分（空格、标点等）
      matches.push({
        text: match[2],
        isWord: false
      })
    }
  }

  return matches
}

// 查询单词
async function lookupWord(word) {
  const cleanWord = word.trim().toLowerCase()
  if (!cleanWord) return

  // 先关闭当前的 Snackbar
  wordLookup.value.snackbar = false

  console.log('查词:', cleanWord)

  try {
    const response = await axios.post(dict_url, {
      word: cleanWord
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    console.log('查词响应:', response.data)

    if (response.data && response.data.length > 0) {
      // 遍历所有结果
      let content = ''
      response.data.forEach((item, index) => {
        if (index > 0) {
          content += '<br>'
        }

        if (item.phonetic) {
          content += `<div style="color: #1976D2; font-weight: bold;">${item.phonetic}</div>`
        }

        if (item.translation) {
          content += `<div>${item.translation}</div>`
        }
      })

      wordLookup.value.content = content || '未找到该单词'
    } else {
      wordLookup.value.content = '未找到该单词'
    }
  } catch (error) {
    console.error('查词失败:', error)
    wordLookup.value.content = '查词失败，请稍后重试'
  }

  console.log('Snackbar 内容:', wordLookup.value.content)

  // 使用 nextTick 等待 DOM 更新，确保计时器重置
  nextTick(() => {
    wordLookup.value.snackbar = true
    console.log('Snackbar 状态:', wordLookup.value.snackbar)
  })
}

// 跳转到指定时间
function seekToTime(time) {
  if (audioplayer) {
    // 尝试使用 shikwasa 的 seek 方法
    if (typeof audioplayer.seek === 'function') {
      audioplayer.seek(time)
    } else {
      console.error('audioplayer.seek 方法不存在')
      console.log('audioplayer 可用方法:', Object.getOwnPropertyNames(Object.getPrototypeOf(audioplayer)))
    }
    console.log('跳转到时间:', time)
  }
}

</script>

<style>
  .container100 {
    width: 100%; /* 确保父元素宽度为 100% */
    /* 其他样式 */
  }
  .padding-top{
    padding-top: 60px; /* 根据需要调整这个值 */
    margin-top: -60px; /* 这个值需要和上面的padding-top相同，但是为负值 */
  }
  .sticky-div {
    position: sticky;
    top: 90px; /* 根据需要调整 */
    z-index: 1000; /* 确保固定div在顶部 */
  }
  .audioplayer {
    width: 100%; /* 让音频元素的宽度铺满父元素 */
  }
  blockquote {
    background: #f9f9f9;
    border-left: 5px solid #ccc;
    padding: 10px;
    margin: 5px 0;
  }
  .bold-text {
    font-weight: bold;
  }

  .v-container {
    padding: 8px;
  }

  .mobile-player-container {
    min-height: calc(100vh - 48px - 56px - 120px);
  }

  blockquote {
    background: #f9f9f9;
    border-left: 5px solid #ccc;
    padding: 8px;
    margin: 3px 0;
  }

  blockquote.text-body-2 {
    font-size: 1rem !important;
  }

  .container100 p {
    font-size: 0.75rem;
  }

  .clickable-word {
    cursor: pointer;
    color: #1976D2;
    border-bottom: 1px dotted #1976D2;
  }

  .clickable-word:hover {
    background-color: #E3F2FD;
  }

  .clickable-time {
    cursor: pointer;
    color: #666666;
    transition: color 0.2s;
  }

  .clickable-time:hover {
    color: #1976D2;
  }

  .clickable-time:active {
    color: #0D47A1;
  }
</style>